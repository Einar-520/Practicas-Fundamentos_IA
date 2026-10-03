"""Rutas de presentación. La validación y las decisiones permanecen en Python."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import request
from comun.ollama_local import OllamaLocal
from logismart.dominio.modelos import (Configuracion, Premisas, Correo, CATEGORIAS, PRIORIDADES,
                                     ESTADOS, CATEGORIAS_ETICAS, validar)
from logismart.dominio.reglas import decidir, tablas
from logismart.infraestructura.configuracion import RAIZ, guardar_configuracion
from logismart.infraestructura.repositorio import COLECCIONES
from logismart.servicios.asistente import responder
from logismart.servicios.clasificador import ClasificadorHibrido
from logismart.servicios.demostracion import cargar_demo
from logismart.servicios.evaluacion import cargar_corpus, evaluar_corpus
from logismart.servicios.notificaciones import notificar
from web.base import crear_base, cuerpo, texto, descargar, exclusivo


def guardar_json(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix('.tmp')
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')
    temporal.replace(ruta)


def crear_app(servicio, directorio=None, guardar_preferencias=guardar_configuracion):
    app, trabajos = crear_base('logistica')
    datos_locales = Path(directorio) if directorio is not None else RAIZ / '.datos'
    corpus_editado = datos_locales / 'correos_revisados.json'
    ultimo_experimento = datos_locales / 'ultimo_experimento.json'

    def ruta_corpus():
        return corpus_editado if corpus_editado.exists() else RAIZ / 'datos/correos_etiquetados.json'

    def coleccion_valida(nombre):
        if nombre not in COLECCIONES:
            raise ValueError('Colección no permitida.')
        return nombre

    def rango():
        return {'desde': request.args.get('desde', ''), 'hasta': request.args.get('hasta', '')}

    def anterior(nombre, datos):
        identificador = datos.pop('id', None)
        version = datos.pop('version', None)
        if identificador is None:
            if version is not None:
                raise ValueError('Selecciona el registro que deseas editar.')
            return None
        if not isinstance(identificador, str) or type(version) is not int or version < 1:
            raise ValueError('Selecciona un registro y una versión válidos.')
        registro = servicio.repo.obtener(nombre, identificador)
        if registro['version'] != version:
            raise ValueError('El registro cambió. Actualiza la tabla antes de guardar.')
        return registro

    @app.get('/api/estado')
    def estado():
        hora = datetime.now(ZoneInfo('America/Mexico_City')).hour
        return {'modo': servicio.repo.modo, 'config': servicio.config.model_dump(),
                'categorias': CATEGORIAS, 'prioridades': PRIORIDADES, 'estados': ESTADOS,
                'categorias_eticas': CATEGORIAS_ETICAS, 'tablas': tablas(),
                'horario_permitido': servicio.config.hora_inicio <= hora < servicio.config.hora_fin,
                'trabajo_activo': trabajos.activo}

    @app.get('/api/panel')
    def panel():
        fechas = rango()
        accesos = servicio.repo.listar('accesos', **fechas)
        return {**servicio.panel(**fechas),
                'ultimos_accesos': accesos[:6],
                'incidentes': servicio.repo.listar('incidentes', **fechas),
                'distribucion': {resultado: sum(d['resultado'] == resultado for d in accesos)
                                for resultado in ('autorizado', 'inspeccion', 'retenido', 'denegado')}}

    @app.get('/api/registros/<nombre>')
    def registros(nombre):
        return {'registros': servicio.repo.listar(coleccion_valida(nombre), **rango())}

    @app.post('/api/registros/<nombre>')
    def guardar(nombre):
        coleccion_valida(nombre)
        datos = cuerpo()
        # Clasificar un correo puede requerir varios segundos: responder con un trabajo.
        if nombre == 'incidentes' and 'id' not in datos:
            correo = validar(Correo, datos)
            return trabajos.iniciar(lambda: servicio.clasificar_correo(correo.model_dump()), 'Clasificando y guardando el correo')
        with trabajos.exclusivo():
            previo = anterior(nombre, datos)
            funciones = {'camiones': servicio.guardar_camion, 'accesos': servicio.guardar_acceso,
                         'riesgos_eticos': servicio.guardar_riesgo,
                         'evaluaciones_llm': servicio.guardar_evaluacion_manual,
                         'incidentes': servicio.editar_incidente}
            if nombre == 'accesos':
                validar(Premisas, {k: datos.get(k) for k in 'PQRSTH'})
            return {'registro': funciones[nombre](datos, previo)}

    @app.delete('/api/registros/<nombre>/<identificador>')
    @exclusivo(trabajos)
    def eliminar(nombre, identificador):
        coleccion_valida(nombre)
        datos = cuerpo()
        if datos.get('confirmar') is not True:
            raise ValueError('Confirma la baja del registro.')
        version = datos.get('version')
        if type(version) is not int or version < 1:
            raise ValueError('La versión del registro no es válida. Actualiza la tabla.')
        servicio.repo.eliminar(nombre, identificador, servicio.config.operador, version)
        return {'mensaje': 'Registro dado de baja. Su historial se conserva para auditoría.'}

    @app.get('/api/camion')
    def buscar_camion():
        return servicio.buscar_placa(request.args.get('placa', ''))

    @app.post('/api/simular')
    def simular():
        return decidir(validar(Premisas, cuerpo()))

    @app.post('/api/asistente')
    def asistente():
        pregunta = texto(cuerpo(), 'pregunta', 3, 1500)
        return trabajos.iniciar(lambda: responder(servicio.repo, servicio.clasificador.cliente,
            pregunta, servicio.config.operador, servicio.config.usar_llm), 'Buscando evidencia en los registros')

    @app.get('/api/asistente/historial')
    def historial_asistente():
        return {'registros': list(reversed(servicio.repo.listar('evaluaciones_llm', {'tipo': 'asistente'})))}

    @app.post('/api/configuracion')
    @exclusivo(trabajos)
    def configuracion():
        config = validar(Configuracion, cuerpo())
        cliente = OllamaLocal(config.modelo, config.url_ollama, config.timeout)
        guardar_preferencias(config)
        servicio.config = config
        servicio.clasificador = ClasificadorHibrido(cliente, config.usar_llm)
        return {'mensaje': 'Configuración guardada.', 'config': config.model_dump()}

    @app.post('/api/conexion')
    def comprobar():
        return trabajos.iniciar(lambda: {'mensaje': servicio.repo.comprobar()}, 'Comprobando el almacenamiento')

    @app.post('/api/demostracion')
    def demostracion():
        if cuerpo().get('confirmar') is not True:
            raise ValueError('Confirma la carga de datos ficticios.')
        def cargar():
            servicio.repo.comprobar()
            return {'mensaje': cargar_demo(servicio)}
        return trabajos.iniciar(cargar, 'Cargando los datos de demostración')

    @app.post('/api/notificar/<identificador>')
    def notificar_incidente(identificador):
        if cuerpo().get('confirmar') is not True:
            raise ValueError('Confirma la notificación a soporte.')
        def tarea():
            incidente = servicio.repo.obtener('incidentes', identificador)
            return {'mensaje': notificar(incidente, servicio.config.simulacion_correo)}
        return trabajos.iniciar(tarea, 'Preparando la notificación')

    @app.get('/api/exportar/<nombre>/<extension>')
    def reporte(nombre, extension):
        filas = servicio.repo.listar(coleccion_valida(nombre), **rango())
        return descargar(filas, extension, f'LogiSmart_{nombre}')

    @app.get('/api/corpus')
    def corpus():
        ruta = ruta_corpus()
        registros = cargar_corpus(ruta)
        return {'registros': registros, 'revision': hashlib.sha256(ruta.read_bytes()).hexdigest(),
                'revisados': sum(d.get('revisado_humano') is True and bool(d.get('revisor')) for d in registros)}

    @app.post('/api/corpus/revisar')
    @exclusivo(trabajos)
    def revisar():
        datos = cuerpo()
        actual = corpus()
        if datos.get('revision') != actual['revision']:
            raise ValueError('El conjunto cambió. Recarga el correo antes de confirmar.')
        if datos.get('categoria_esperada') not in CATEGORIAS or datos.get('prioridad_esperada') not in PRIORIDADES:
            raise ValueError('Elige una categoría y una prioridad válidas.')
        if type(datos.get('revisado_humano')) is not bool:
            raise ValueError('Indica si ya revisaste personalmente este correo.')
        registro = next((d for d in actual['registros'] if d['id'] == datos.get('id')), None)
        if registro is None:
            raise ValueError('Correo no encontrado.')
        for campo in ('categoria_esperada', 'prioridad_esperada', 'revisado_humano'):
            registro[campo] = datos[campo]
        registro['revisor'] = servicio.config.operador if datos['revisado_humano'] else ''
        guardar_json(corpus_editado, actual['registros'])
        return corpus()

    @app.get('/api/corpus/exportar')
    def exportar_corpus():
        return descargar(cargar_corpus(ruta_corpus()), 'json', 'correos_revisados')

    @app.post('/api/corpus/importar')
    @exclusivo(trabajos)
    def importar_corpus():
        from tempfile import TemporaryDirectory
        datos = cuerpo()
        if datos.get('confirmar') is not True or not isinstance(datos.get('registros'), list) or len(datos['registros']) > 1000:
            raise ValueError('Confirma la importación de un conjunto de 30 a 1000 correos.')
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'corpus.json'
            guardar_json(ruta, datos['registros'])
            registros = cargar_corpus(ruta)
        guardar_json(corpus_editado, registros)
        return corpus()

    @app.post('/api/experimento')
    def experimento():
        solo_reglas = cuerpo().get('solo_reglas', False)
        if type(solo_reglas) is not bool:
            raise ValueError('Selecciona un modo válido de evaluación.')
        def tarea():
            motor = ClasificadorHibrido(servicio.clasificador.cliente, not solo_reglas)
            resultado = evaluar_corpus(ruta_corpus(), motor, servicio.repo, servicio.config.operador)
            guardar_json(ultimo_experimento, resultado)
            return resultado
        return trabajos.iniciar(tarea, 'Evaluando los correos; puede tardar varios minutos')

    @app.get('/api/experimento')
    def ultimo():
        return {'resultado': json.loads(ultimo_experimento.read_text(encoding='utf-8')) if ultimo_experimento.exists() else None}

    @app.get('/api/experimento/exportar/<extension>')
    def exportar_experimento(extension):
        datos = ultimo()['resultado']
        if datos is None:
            raise ValueError('Ejecuta primero una comparación.')
        return descargar(datos, extension, 'experimento_clasificacion')

    return app
