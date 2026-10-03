"""Servidor local, respuestas uniformes y trabajos que no bloquean la página."""
import copy
import secrets
import threading
from collections import OrderedDict
from contextlib import contextmanager
from functools import wraps
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import HTTPException
from logismart.servicios.reportes import exportar


class Ocupado(RuntimeError):
    pass


class Trabajos:
    def __init__(self):
        self.operacion = threading.Lock()
        self.lock = threading.Lock()
        self.registros = OrderedDict()
        self.activo = None

    @contextmanager
    def exclusivo(self):
        if not self.operacion.acquire(blocking=False):
            raise Ocupado('Hay una operación en curso. Espera a que termine antes de guardar otra.')
        try:
            yield
        finally:
            self.operacion.release()

    def iniciar(self, tarea, titulo):
        if not self.operacion.acquire(blocking=False):
            raise Ocupado('Ya hay una operación en curso. Puedes seguir consultando las pantallas.')
        identificador = secrets.token_hex(16)
        with self.lock:
            self.registros[identificador] = {'id': identificador, 'titulo': titulo, 'estado': 'en_proceso'}
            self.activo = identificador
            while len(self.registros) > 20:
                self.registros.popitem(last=False)

        def trabajar():
            try:
                resultado = {'estado': 'completado', 'resultado': tarea()}
            except (ValueError, RuntimeError) as error:
                resultado = {'estado': 'error', 'error': str(error)}
            except Exception:
                resultado = {'estado': 'error', 'error': 'No se completó la operación. Revisa la conexión y vuelve a consultar los registros.'}
            finally:
                # El resultado queda disponible incluso si la pestaña se recarga.
                with self.lock:
                    self.registros[identificador].update(resultado)
                    self.activo = None
                self.operacion.release()

        threading.Thread(target=trabajar, daemon=True).start()
        return {'trabajo': identificador}, 202

    def obtener(self, identificador):
        with self.lock:
            if identificador not in self.registros:
                raise ValueError('La operación ya no está disponible. Consulta los registros actualizados.')
            return copy.deepcopy(self.registros[identificador])


def cuerpo():
    datos = request.get_json()
    if not isinstance(datos, dict):
        raise ValueError('El formulario debe contener un objeto de datos.')
    return datos


def texto(datos, clave, minimo=1, maximo=2000):
    valor = datos.get(clave)
    if not isinstance(valor, str) or not minimo <= len(valor.strip()) <= maximo:
        raise ValueError(f'El campo {clave} debe tener entre {minimo} y {maximo} caracteres.')
    return valor.strip()


def descargar(datos, extension, nombre):
    if extension not in {'json', 'csv', 'pdf'}:
        raise ValueError('Elige PDF, CSV o JSON.')
    with TemporaryDirectory() as temporal:
        ruta = Path(temporal) / f'{nombre}.{extension}'
        exportar(datos, ruta, nombre.replace('_', ' '))
        contenido = ruta.read_bytes()
    tipos = {'json': 'application/json', 'csv': 'text/csv', 'pdf': 'application/pdf'}
    return send_file(BytesIO(contenido), mimetype=tipos[extension], as_attachment=True,
                     download_name=f'{nombre}.{extension}', max_age=0)


def crear_base(ejercicio):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.json.ensure_ascii = False
    app.config.update(MAX_CONTENT_LENGTH=2_000_000, TRUSTED_HOSTS=['localhost', '127.0.0.1', '[::1]'])
    token = secrets.token_urlsafe(32)
    trabajos = Trabajos()
    app.extensions['trabajos'] = trabajos

    @app.before_request
    def proteger():
        if request.headers.get('Sec-Fetch-Site') == 'cross-site':
            return jsonify(error='Abre la aplicación directamente desde localhost.'), 403
        if request.path.startswith('/api/'):
            recibido = request.headers.get('X-CSRF-Token', '')
            if not secrets.compare_digest(recibido, token):
                return jsonify(error='Recarga la página para renovar la sesión local.'), 403

    @app.after_request
    def cabeceras(respuesta):
        respuesta.headers['Cache-Control'] = 'no-store'
        respuesta.headers['X-Content-Type-Options'] = 'nosniff'
        respuesta.headers['X-Frame-Options'] = 'DENY'
        respuesta.headers['Referrer-Policy'] = 'same-origin'
        respuesta.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        return respuesta

    @app.errorhandler(Exception)
    def error_amigable(error):
        if isinstance(error, Ocupado):
            return jsonify(error=str(error)), 409
        if isinstance(error, (ValueError, TypeError)):
            return jsonify(error=str(error) if isinstance(error, ValueError) else 'Revisa los tipos del formulario.'), 400
        if isinstance(error, RuntimeError):
            return jsonify(error=str(error)), 503
        if isinstance(error, HTTPException):
            return jsonify(error='Solicitud no válida o recurso no disponible.'), error.code
        app.logger.error('Error de aplicación: %s', type(error).__name__)
        return jsonify(error='No se pudo completar la operación. Revisa la conexión y vuelve a consultar.'), 500

    @app.get('/')
    def inicio():
        return render_template(f'{ejercicio}.html', token=token)

    @app.get('/api/trabajos/<identificador>')
    def estado_trabajo(identificador):
        return trabajos.obtener(identificador)

    return app, trabajos


def exclusivo(trabajos):
    def decorar(funcion):
        @wraps(funcion)
        def ejecutar(*args, **kwargs):
            with trabajos.exclusivo():
                return funcion(*args, **kwargs)
        return ejecutar
    return decorar


def servir(app, puerto):
    if not 1024 <= puerto <= 65535:
        raise ValueError('El puerto debe estar entre 1024 y 65535.')
    print(f'Abre http://localhost:{puerto} en tu navegador. Detén el servidor con Ctrl+C.')
    app.run(host='127.0.0.1', port=puerto, debug=False, use_reloader=False, threaded=True)
