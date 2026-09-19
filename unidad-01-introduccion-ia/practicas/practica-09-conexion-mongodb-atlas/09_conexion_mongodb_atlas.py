"""Práctica 9: interfaz web local y conexión privada con MongoDB Atlas."""

import atexit
import secrets
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

from servicio_atlas import ErrorAtlas, ServicioAtlas

DIRECTORIO = Path(__file__).resolve().parent


def crear_app(coleccion=None):
    """Permitir una colección simulada para probar sin acceder al clúster."""
    app = Flask(__name__, template_folder=str(DIRECTORIO / "templates"),
                static_folder=str(DIRECTORIO / "static"))
    app.config.update(SECRET_KEY=secrets.token_hex(32), MAX_CONTENT_LENGTH=16384,
                      SESSION_COOKIE_NAME="practica_9_sesion",
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict")
    servicio = ServicioAtlas(coleccion)
    atexit.register(servicio.cerrar)
    try:
        servicio.abrir()
    except ErrorAtlas:
        pass  # La API explica el error y permite reintentar al corregir el .env.

    def error_json(mensaje, estado=503, **extras):
        return jsonify(ok=False, mensaje=mensaje, **extras), estado

    @app.errorhandler(ErrorAtlas)
    def error_atlas(error):
        extras = {"guardado": True} if error.guardado else {}
        return error_json(str(error), error.codigo, **extras)

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
        return render_template("index.html", base=servicio.base, coleccion=servicio.coleccion)

    @app.get("/api/documento")
    def consultar():
        return jsonify(ok=True, documento=servicio.consultar())

    @app.post("/api/documento")
    def guardar():
        token = request.form.get("csrf", "")
        esperado = session.get("csrf", "")
        if not token or not secrets.compare_digest(token.encode(), esperado.encode()):
            return error_json("El formulario expiró. Recarga la página e inténtalo de nuevo.", 400)
        return jsonify(servicio.guardar(request.form.get("dato", "")))

    @app.errorhandler(413)
    def contenido_grande(error):
        return error_json("El formulario es demasiado grande. Escribe hasta 1000 caracteres.", 413)

    return app


if __name__ == "__main__":
    print("Abre http://localhost:5001 en tu navegador. Detén la página con Ctrl+C.")
    crear_app().run(host="127.0.0.1", port=5001, debug=False)
