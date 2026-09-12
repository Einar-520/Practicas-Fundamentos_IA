"""Práctica 8: interfaz web local para guardar y consultar en MongoDB."""

import atexit
import re
import secrets
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

URI_MONGODB = "mongodb://127.0.0.1:27017/"
BASE_DATOS = "fundamentos_ia"
COLECCION = "practicas"
DIRECTORIO = Path(__file__).resolve().parent


def validar(datos):
    """Validar también en Python, aunque el navegador valide el formulario."""
    numero = datos["numero"]
    if not re.fullmatch(r"[0-9]{1,19}", numero):
        raise ValueError("El número debe ser un entero positivo.")
    numero = int(numero)
    if not 1 <= numero <= 9223372036854775807:
        raise ValueError("El número está fuera del rango permitido.")
    if not 1 <= len(datos["nombre"]) <= 120:
        raise ValueError("Escribe un nombre de entre 1 y 120 caracteres.")
    if not 1 <= len(datos["lenguaje"]) <= 40:
        raise ValueError("Escribe un lenguaje de entre 1 y 40 caracteres.")
    return numero, {"nombre": datos["nombre"], "lenguaje": datos["lenguaje"]}


def crear_app(coleccion=None):
    app = Flask(__name__, template_folder=str(DIRECTORIO / "templates"),
                static_folder=str(DIRECTORIO / "static"))
    app.config.update(SECRET_KEY=secrets.token_hex(32), MAX_CONTENT_LENGTH=16384,
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

    if coleccion is None:
        cliente = MongoClient(URI_MONGODB, serverSelectionTimeoutMS=3000,
                              connectTimeoutMS=3000, socketTimeoutMS=3000)
        atexit.register(cliente.close)
        coleccion = cliente[BASE_DATOS][COLECCION]

        # --- INYECCIÓN EN EL BACKEND ---
        try:
            coleccion.update_one(
                {"_id": 1}, 
                {"$set": {"nombre": "Wazaaaaaaa", "lenguaje": "Desconocido"}},
                upsert=True
            )
            print("¡Dato 'Wazaaaaaaa' validado/insertado correctamente en MongoDB al iniciar!")
        except PyMongoError as e:
            print(f"No se pudo insertar el dato inicial: {e}")
        # -------------------------------

    def pagina(datos=None, error=None, estado=200):
        session.setdefault("csrf", secrets.token_hex(32))
        try:
            registros = list(coleccion.find({}, {"nombre": 1, "lenguaje": 1})
                             .sort("_id", 1).limit(100))
            conectado = True
        except PyMongoError:
            registros, conectado = [], False
            error = error or "No se pudo consultar MongoDB. Comprueba el servidor y los permisos."
            estado = 503
        return render_template("index.html", registros=registros, conectado=conectado,
                               error=error, datos=datos or {"numero": "8", "nombre": "Conexión con MongoDB", "lenguaje": "Python"}), estado

    @app.get("/")
    def inicio():
        return pagina()

    @app.post("/guardar")
    def guardar():
        datos = {campo: request.form.get(campo, "").strip()
                 for campo in ("numero", "nombre", "lenguaje")}
        token = request.form.get("csrf", "")
        if not token or not secrets.compare_digest(token.encode(), session.get("csrf", "").encode()):
            return pagina(datos, "El formulario expiró. Vuelve a enviarlo desde esta página.", 400)
        try:
            numero, documento = validar(datos)
        except ValueError as error:
            return pagina(datos, str(error), 400)

        try:
            resultado = coleccion.update_one({"_id": numero}, {"$set": documento}, upsert=True)
        except ConnectionFailure:
            return pagina(datos, "Se interrumpió la comunicación con MongoDB. Consulta los registros antes de reintentar.", 503)
        except PyMongoError:
            return pagina(datos, "No se pudo completar el guardado. Revisa los permisos de MongoDB.", 503)

        if resultado.upserted_id is not None:
            mensaje = f"Práctica {numero} guardada correctamente."
        elif resultado.modified_count:
            mensaje = f"Práctica {numero} actualizada correctamente."
        else:
            mensaje = f"La práctica {numero} ya contiene esos datos."
        flash(mensaje)
        return redirect(url_for("inicio"), code=303)

    @app.errorhandler(413)
    def formulario_grande(error):
        return pagina(error="El formulario es demasiado grande.", estado=413)

    return app


if __name__ == "__main__":
    print("Abre http://localhost:5000 en tu navegador. Detén la página con Ctrl+C.")
    crear_app().run(host="127.0.0.1", port=5000, debug=False)