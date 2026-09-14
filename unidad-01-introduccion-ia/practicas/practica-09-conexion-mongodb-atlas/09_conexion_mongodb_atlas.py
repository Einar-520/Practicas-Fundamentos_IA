"""Práctica 9: interfaz web local y conexión privada con MongoDB Atlas."""

import atexit
import secrets
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure, OperationFailure, PyMongoError

from configuracion import cargar_configuracion

DIRECTORIO = Path(__file__).resolve().parent
FILTRO = {"_id": "practica_09"}
PROYECCION = {"nombre": 1, "practica": 1, "dato": 1, "actualizado_en": 1}


def mensaje_error(error):
    """Traducir errores conocidos sin publicar la URI ni mensajes del driver."""
    if isinstance(error, OperationFailure):
        if error.code == 18:
            return "Atlas rechazó las credenciales. Revisa el usuario y la contraseña en tu .env."
        if error.code == 13:
            return "Faltan permisos. Pide al profesor acceso de lectura y escritura a tu base."
        return "Atlas rechazó la operación. Revisa los permisos con el profesor."
    if isinstance(error, ConfigurationError):
        return "No se pudo configurar Atlas. Revisa el dominio del clúster y la resolución DNS."
    if isinstance(error, ConnectionFailure):
        return "No hay comunicación con Atlas. Comprueba Internet y que tu IP esté autorizada."
    return "No se pudo completar la operación en MongoDB Atlas."


def serializar(documento):
    if documento is None:
        return None
    fecha = documento.get("actualizado_en")
    if isinstance(fecha, datetime):
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        fecha = fecha.isoformat()
    else:
        fecha = None
    return {"id": str(documento["_id"]),
            "nombre": str(documento.get("nombre", "")),
            "practica": 9, "dato": str(documento.get("dato", "")),
            "actualizado_en": fecha}


def crear_app(coleccion=None):
    """Permitir una colección simulada para probar sin acceder al clúster."""
    app = Flask(__name__, template_folder=str(DIRECTORIO / "templates"),
                static_folder=str(DIRECTORIO / "static"))
    app.config.update(SECRET_KEY=secrets.token_hex(32), MAX_CONTENT_LENGTH=16384,
                      SESSION_COOKIE_NAME="practica_9_sesion",
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict")
    error_configuracion = None
    mongo_db, mongo_collection = "", ""
    cliente = None
    if coleccion is None:
        try:
            # El enlace se construye en Python y nunca se envía al navegador.
            mongo_url, mongo_db, mongo_collection = cargar_configuracion()
        except ValueError as error:
            error_configuracion = str(error)  # Mensaje controlado de configuracion.py.
        else:
            try:
                cliente = MongoClient(mongo_url, serverSelectionTimeoutMS=10000,
                                      connectTimeoutMS=10000, socketTimeoutMS=10000,
                                      maxPoolSize=5, tz_aware=True)
                coleccion = cliente[mongo_db][mongo_collection]
                atexit.register(cliente.close)
            except (PyMongoError, ValueError) as error:
                error_configuracion = mensaje_error(error)
                if cliente is not None:
                    cliente.close()
    else:
        mongo_db, mongo_collection = "Einar_Ivan_Lazcano_Luna", "datos"

    def error_json(mensaje, estado=503, **extras):
        return jsonify(ok=False, mensaje=mensaje, **extras), estado

    @app.after_request
    def cabeceras(respuesta):
        respuesta.headers["Cache-Control"] = "no-store"
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; base-uri 'none'; "
            "form-action 'self'; frame-ancestors 'none'"
        )
        return respuesta

    @app.get("/")
    def inicio():
        session.setdefault("csrf", secrets.token_hex(32))
        return render_template("index.html", base=mongo_db, coleccion=mongo_collection)

    @app.get("/api/documento")
    def consultar():
        if error_configuracion:
            return error_json(error_configuracion)
        try:
            documento = coleccion.find_one(FILTRO, PROYECCION)
            return jsonify(ok=True, documento=serializar(documento))
        except PyMongoError as error:
            return error_json(mensaje_error(error))

    @app.post("/api/documento")
    def guardar():
        token = request.form.get("csrf", "")
        esperado = session.get("csrf", "")
        if not token or not secrets.compare_digest(token.encode(), esperado.encode()):
            return error_json("El formulario expiró. Recarga la página e inténtalo de nuevo.", 400)
        dato = request.form.get("dato", "").strip()
        if not 1 <= len(dato) <= 1000:
            return error_json("Escribe un dato de entre 1 y 1000 caracteres.", 400)
        if error_configuracion:
            return error_json(error_configuracion)
        documento = {"nombre": "Einar Ivan Lazcano Luna", "practica": 9,
                     "dato": dato, "actualizado_en": datetime.now(timezone.utc)}
        try:
            resultado = coleccion.update_one(FILTRO, {"$set": documento}, upsert=True)
        except PyMongoError as error:
            return error_json(mensaje_error(error) + " Consulta el documento antes de reintentar el guardado.")

        # Diferenciar una escritura confirmada de una consulta posterior fallida.
        mensaje = ("Tu dato se guardó en Atlas." if resultado.upserted_id is not None
                   else "Tu dato se actualizó en Atlas.")
        try:
            guardado = coleccion.find_one(FILTRO, PROYECCION)
        except PyMongoError:
            return error_json("El guardado se confirmó, pero no se pudo consultar el resultado. Pulsa Actualizar.", guardado=True)
        if guardado is None:
            return error_json("El guardado se confirmó, pero el documento ya no aparece. Pulsa Actualizar.", guardado=True)
        return jsonify(ok=True, mensaje=mensaje, documento=serializar(guardado))

    @app.errorhandler(413)
    def contenido_grande(error):
        return error_json("El formulario es demasiado grande. Escribe hasta 1000 caracteres.", 413)

    return app


if __name__ == "__main__":
    print("Abre http://localhost:5001 en tu navegador. Detén la página con Ctrl+C.")
    crear_app().run(host="127.0.0.1", port=5001, debug=False)
