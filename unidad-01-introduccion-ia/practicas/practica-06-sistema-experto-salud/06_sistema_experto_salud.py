"""Práctica 6: interfaz independiente; reglas originales conservadas."""


from pathlib import Path
import secrets
from math import isfinite

from flask import Flask, jsonify, render_template, request, session
def evaluar_sintomas(fiebre: bool, tos: bool, dolor_garganta: bool) -> str:
    """Devolver el primer resultado aplicable, con la prioridad original."""
    if fiebre and tos:
        return "Posible infección respiratoria"
    if tos and dolor_garganta:
        return "Posible irritación respiratoria"
    if fiebre:
        return "Se recomienda valoración profesional"
    return "No se identificó un patrón"

NUMERO = 6
PUERTO = 5106
TITULO = 'Sistema experto de salud'
DESCRIPCION = 'Ejercicio académico de tres síntomas. El resultado es orientativo y no sustituye una valoración médica.'
GRUPOS = [{'titulo': 'Síntomas',
  'campos': [{'clave': 'fiebre', 'etiqueta': '¿Tiene fiebre?', 'tipo': 'booleano'},
             {'clave': 'tos', 'etiqueta': '¿Tiene tos?', 'tipo': 'booleano'},
             {'clave': 'dolor_garganta',
              'etiqueta': '¿Tiene dolor de garganta?',
              'tipo': 'booleano'}]}]
BOTON = 'Evaluar síntomas'


def evaluar(datos):
    return {"titulo": evaluar_sintomas(**datos), "clase": "neutral",
            "mensajes": ["Resultado orientativo de las reglas de la práctica."], "tablas": []}



def leer_formulario(formulario):
    datos = {}
    for grupo in GRUPOS:
        for campo in grupo["campos"]:
            clave = campo["clave"]
            valor = formulario.get(clave, "").strip()
            if not valor:
                raise ValueError(f"Completa el campo: {campo['etiqueta']}.")
            if campo["tipo"] == "booleano":
                if valor not in ("si", "no"):
                    raise ValueError(f"Selecciona Sí o No en: {campo['etiqueta']}.")
                datos[clave] = valor == "si"
            elif campo["tipo"] == "numero":
                try:
                    numero = float(valor)
                except ValueError:
                    raise ValueError(f"Ingresa un número válido en: {campo['etiqueta']}.") from None
                if not isfinite(numero):
                    raise ValueError(f"El número de {campo['etiqueta']} debe ser finito.")
                datos[clave] = numero
            elif campo["tipo"] == "opcion":
                if valor not in campo["opciones"]:
                    raise ValueError(f"Selecciona una opción válida en: {campo['etiqueta']}.")
                datos[clave] = valor
            else:
                datos[clave] = valor
    return datos

def crear_app():
    raiz = Path(__file__).resolve().parent
    app = Flask(__name__, template_folder=str(raiz / "templates"), static_folder=str(raiz / "static"))
    app.config.update(SECRET_KEY=secrets.token_hex(32), SESSION_COOKIE_NAME=f"practica_{NUMERO}_sesion", SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE="Strict", MAX_CONTENT_LENGTH=131072)

    @app.after_request
    def proteger(respuesta):
        respuesta.headers["Cache-Control"] = "no-store"
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        return respuesta

    @app.get("/")
    def inicio():
        session.setdefault("csrf", secrets.token_hex(32))
        return render_template("index.html", numero=NUMERO, titulo=TITULO, descripcion=DESCRIPCION, grupos=GRUPOS, boton=BOTON)

    @app.post("/evaluar")
    def procesar():
        token = request.form.get("csrf", "")
        if not token or not secrets.compare_digest(token.encode(), session.get("csrf", "").encode()):
            return jsonify(ok=False, mensaje="El formulario expiró. Recarga la página."), 400
        try:
            datos = leer_formulario(request.form)
        except ValueError as error:
            return jsonify(ok=False, mensaje=str(error)), 400
        return jsonify(ok=True, resultado=evaluar(datos))

    @app.errorhandler(413)
    def demasiado_grande(error):
        return jsonify(ok=False, mensaje="El formulario es demasiado grande. Reduce el texto e inténtalo de nuevo."), 413

    return app

if __name__ == "__main__":
    print(f"Abre http://localhost:{PUERTO} en tu navegador. Detén el servidor con Ctrl+C.")
    crear_app().run(host="127.0.0.1", port=PUERTO, debug=False)
