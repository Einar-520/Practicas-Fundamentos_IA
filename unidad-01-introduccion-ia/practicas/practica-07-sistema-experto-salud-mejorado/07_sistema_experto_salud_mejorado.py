"""Práctica 7: interfaz independiente; reglas originales conservadas."""


from pathlib import Path
import secrets
from math import isfinite

from flask import Flask, jsonify, render_template, request, session
from dataclasses import dataclass

@dataclass(frozen=True)
class Regla:
    """Agrupar las condiciones y los tres textos de una regla académica."""

    sintomas_requeridos: tuple[str, ...]
    diagnostico: str
    recomendacion: str
    descripcion: str

PREGUNTAS = (
    ("fiebre", "¿Tiene fiebre? (s/n): "),
    ("tos", "¿Tiene tos? (s/n): "),
    ("dolor_garganta", "¿Tiene dolor de garganta? (s/n): "),
    ("congestion", "¿Tiene congestión nasal? (s/n): "),
    ("dolor_cabeza", "¿Tiene dolor de cabeza? (s/n): "),
    ("cansancio", "¿Presenta cansancio? (s/n): "),
    ("dificultad_respirar", "¿Tiene dificultad para respirar? (s/n): "),
)

REGLAS = (
    Regla(
        sintomas_requeridos=("dificultad_respirar",),
        diagnostico="Se detectó dificultad para respirar.",
        recomendacion=(
            "Se recomienda buscar valoración profesional de forma prioritaria."
        ),
        descripcion="Regla 1: dificultad respiratoria",
    ),
    Regla(
        sintomas_requeridos=("fiebre", "tos", "cansancio"),
        diagnostico="Patrón de síntomas respiratorios con fiebre y cansancio.",
        recomendacion="Se recomienda valoración profesional.",
        descripcion="Regla 2: fiebre AND tos AND cansancio",
    ),
    Regla(
        sintomas_requeridos=("tos", "dolor_garganta", "congestion"),
        diagnostico="Patrón de irritación de vías respiratorias.",
        recomendacion=(
            "Dar seguimiento a los síntomas y considerar valoración profesional."
        ),
        descripcion="Regla 3: tos AND dolor de garganta AND congestión",
    ),
    Regla(
        sintomas_requeridos=("fiebre", "dolor_cabeza"),
        diagnostico="Fiebre acompañada de dolor de cabeza.",
        recomendacion="Vigilar los síntomas y solicitar valoración si continúan.",
        descripcion="Regla 4: fiebre AND dolor de cabeza",
    ),
    Regla(
        sintomas_requeridos=("congestion", "dolor_garganta"),
        diagnostico="Molestias en vías respiratorias superiores.",
        recomendacion="Mantener vigilancia de los síntomas.",
        descripcion="Regla 5: congestión AND dolor de garganta",
    ),
    Regla(
        sintomas_requeridos=("fiebre",),
        diagnostico="Fiebre sin un patrón adicional suficiente.",
        recomendacion=(
            "Se recomienda valoración profesional si la fiebre persiste."
        ),
        descripcion="Regla 6: fiebre",
    ),
)

REGLA_POR_DEFECTO = Regla(
    sintomas_requeridos=(),
    diagnostico="No se identificó un patrón con las reglas actuales.",
    recomendacion="Continuar observando los síntomas.",
    descripcion="Regla por defecto",
)

def evaluar_sintomas(sintomas: dict[str, bool]) -> Regla:
    """Seleccionar la primera regla cuyos síntomas requeridos estén presentes."""
    for regla in REGLAS:
        if all(sintomas[sintoma] for sintoma in regla.sintomas_requeridos):
            return regla
    return REGLA_POR_DEFECTO

NUMERO = 7
PUERTO = 5107
TITULO = 'Sistema experto de salud mejorado'
DESCRIPCION = 'Esta práctica académica evalúa siete síntomas y explica la regla activada. No sustituye una valoración médica.'
GRUPOS = [{'titulo': 'Síntomas',
  'campos': [{'clave': 'fiebre', 'etiqueta': '¿Tiene fiebre?', 'tipo': 'booleano'},
             {'clave': 'tos', 'etiqueta': '¿Tiene tos?', 'tipo': 'booleano'},
             {'clave': 'dolor_garganta',
              'etiqueta': '¿Tiene dolor de garganta?',
              'tipo': 'booleano'},
             {'clave': 'congestion',
              'etiqueta': '¿Tiene congestión nasal?',
              'tipo': 'booleano'},
             {'clave': 'dolor_cabeza',
              'etiqueta': '¿Tiene dolor de cabeza?',
              'tipo': 'booleano'},
             {'clave': 'cansancio',
              'etiqueta': '¿Presenta cansancio?',
              'tipo': 'booleano'},
             {'clave': 'dificultad_respirar',
              'etiqueta': '¿Tiene dificultad para respirar?',
              'tipo': 'booleano'}]}]
BOTON = 'Evaluar y explicar'


def evaluar(datos):
    regla = evaluar_sintomas(datos)
    return {"titulo": regla.diagnostico, "clase": "neutral",
            "mensajes": [regla.descripcion, "Recomendación: " + regla.recomendacion], "tablas": []}



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
