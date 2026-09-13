"""Práctica 4: interfaz independiente; reglas originales conservadas."""


from pathlib import Path
import secrets
from math import isfinite

from flask import Flask, jsonify, render_template, request, session
TIPOS_EQUIPO = ("pc", "laptop", "servidor", "tablet")

def diagnosticar_equipo(electricidad: bool, enciende: bool, imagen: bool) -> str:
    """Aplicar la primera condición que corresponda, en el orden original."""
    if not electricidad:
        return "El equipo NO recibe electricidad."
    if not enciende:
        return "El equipo tiene electricidad, pero NO enciende."
    if not imagen:
        return "El equipo enciende, pero NO muestra imagen."
    return "El equipo funciona correctamente."

NUMERO = 4
PUERTO = 5104
TITULO = 'Diagnóstico de equipo'
DESCRIPCION = 'Evalúa electricidad, encendido, imagen y presencia de daños físicos.'
GRUPOS = [{'titulo': 'Equipo',
  'campos': [{'clave': 'modelo', 'etiqueta': 'Modelo del equipo', 'tipo': 'texto'},
             {'clave': 'tipo_equipo',
              'etiqueta': 'Tipo de equipo',
              'tipo': 'opcion',
              'opciones': {'pc': 'PC',
                           'laptop': 'Laptop',
                           'servidor': 'Servidor',
                           'tablet': 'Tablet'}}]},
 {'titulo': 'Estado del equipo',
  'campos': [{'clave': 'electricidad',
              'etiqueta': '¿Tiene electricidad?',
              'tipo': 'booleano'},
             {'clave': 'enciende', 'etiqueta': '¿Enciende?', 'tipo': 'booleano'},
             {'clave': 'imagen', 'etiqueta': '¿Muestra imagen?', 'tipo': 'booleano'},
             {'clave': 'golpes', 'etiqueta': '¿Recibió golpes?', 'tipo': 'booleano'},
             {'clave': 'agua', 'etiqueta': '¿Le cayó agua?', 'tipo': 'booleano'},
             {'clave': 'otro_dano',
              'etiqueta': '¿Tiene otro daño visible?',
              'tipo': 'booleano'}]}]
BOTON = 'Diagnosticar equipo'


def evaluar(datos):
    diagnostico = diagnosticar_equipo(datos["electricidad"], datos["enciende"], datos["imagen"])
    dano = datos["golpes"] or datos["agua"] or datos["otro_dano"]
    mensajes = [f"Equipo: {datos['modelo']} ({datos['tipo_equipo']})"]
    if dano:
        mensajes.append("También se detectó daño físico.")
    correcto = datos["electricidad"] and datos["enciende"] and datos["imagen"] and not dano
    return {"titulo": diagnostico, "clase": "positivo" if correcto else "aviso", "mensajes": mensajes, "tablas": []}



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
