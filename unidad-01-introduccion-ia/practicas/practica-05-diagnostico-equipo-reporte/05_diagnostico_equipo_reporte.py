"""Práctica 5: interfaz independiente; reglas originales conservadas."""


from pathlib import Path
import secrets
from math import isfinite

from flask import Flask, jsonify, render_template, request, session
import random

from dataclasses import dataclass

from datetime import datetime

TIPOS_EQUIPO = {"pc": "PC", "laptop": "Laptop", "servidor": "Servidor", "tablet": "Tablet"}

TIPOS_DISCO = {
    "hdd": "Disco duro HDD",
    "ssd": "Disco de estado sólido SSD",
    "otro": "Otro tipo de almacenamiento",
}

PROCESADORES = {"intel": "Intel", "amd": "AMD", "arm": "ARM", "otro": "Otro"}

PREGUNTAS = (
    ("electricidad", "P", "¿El equipo tiene electricidad?", "Tiene electricidad"),
    ("enciende", "Q", "¿El equipo enciende?", "Enciende"),
    ("imagen", "R", "¿El equipo muestra imagen?", "Muestra imagen"),
    ("sistema_inicia", "S", "¿El sistema operativo inicia correctamente?", "Inicia sistema operativo"),
    ("se_reinicia", "T", "¿El equipo se reinicia o apaga solo?", "Se reinicia solo"),
    ("sobrecalentamiento", "U", "¿El equipo se calienta demasiado?", "Sobrecalentamiento"),
    ("ruido", "V", "¿El equipo hace ruidos extraños?", "Ruidos extraños"),
    ("lento", "W", "¿El equipo funciona muy lento?", "Funciona lento"),
    ("internet", "X", "¿El equipo puede conectarse a Internet?", "Tiene Internet"),
    ("usb", "Y", "¿Los puertos USB funcionan correctamente?", "USB funciona"),
    ("audio", "Z", "¿El equipo reproduce sonido correctamente?", "Audio funciona"),
    ("golpes", "", "¿El equipo recibió golpes?", "Recibió golpes"),
    ("agua", "", "¿Al equipo le cayó agua?", "Tuvo contacto con agua"),
    ("otro_dano", "", "¿El equipo tiene algún otro daño visible?", "Otro daño visible"),
)

OBSERVACIONES = (
    ("se_reinicia", True, "El equipo se reinicia o apaga solo.",
     "Puede estar relacionado con temperatura, energía o componentes internos."),
    ("sobrecalentamiento", True, "El equipo presenta sobrecalentamiento.",
     "Revisar ventilación, ventiladores y mantenimiento."),
    ("ruido", True, "El equipo presenta ruidos extraños.",
     "Revisar ventiladores o unidades de almacenamiento."),
    ("lento", True, "El equipo presenta lentitud.",
     "Revisar memoria RAM, almacenamiento y funcionamiento del sistema."),
    ("internet", False, "El equipo no tiene conexión a Internet.",
     "Revisar Wi-Fi, cable de red o configuración de red."),
    ("usb", False, "Los puertos USB presentan problemas.", ""),
    ("audio", False, "El sistema de audio presenta problemas.", ""),
    ("golpes", True, "El equipo recibió golpes.", ""),
    ("agua", True, "El equipo tuvo contacto con agua.", ""),
    ("otro_dano", True, "El equipo presenta otro daño físico visible.", ""),
)

@dataclass(frozen=True)
class Evaluacion:
    funcionamiento_basico: bool
    dano_fisico: bool
    respuestas_consistentes: bool
    equipo_correcto: bool
    diagnostico: str
    recomendacion: str
    observaciones: tuple[tuple[str, str], ...]

def si_no(valor: bool) -> str:
    return "Sí" if valor else "No"

def evaluar_equipo(estado: dict[str, bool]) -> Evaluacion:
    p = estado["electricidad"]
    q = estado["enciende"]
    r = estado["imagen"]
    s = estado["sistema_inicia"]

    # Estas implicaciones se utilizaban sin estar definidas en el original.
    q_implica_p = (not q) or p
    r_implica_q = (not r) or q
    sistema_consistente = (not s) or (q and r)
    consistentes = q_implica_p and r_implica_q and sistema_consistente
    dano_fisico = estado["golpes"] or estado["agua"] or estado["otro_dano"]

    if not consistentes:
        diagnostico = "Las respuestas proporcionadas son contradictorias."
        recomendacion = "Revisa las respuestas proporcionadas e intenta nuevamente."
    elif not p:
        diagnostico = "El equipo NO recibe electricidad."
        recomendacion = "Revisar cable de corriente, cargador, fuente de poder o conexión eléctrica."
    elif not q:
        diagnostico = "El equipo recibe electricidad, pero NO enciende."
        recomendacion = "Posible problema de fuente de poder, batería o componentes internos."
    elif not r:
        diagnostico = "El equipo enciende, pero NO muestra imagen."
        recomendacion = "Revisar monitor, pantalla, cable de video o componentes de video."
    elif not s:
        diagnostico = "El equipo enciende y muestra imagen, pero el sistema operativo NO inicia."
        recomendacion = "Posible problema del sistema operativo o almacenamiento."
    else:
        diagnostico = "El funcionamiento básico es correcto."
        recomendacion = ""

    sin_fallas_adicionales = (
        not estado["se_reinicia"]
        and not estado["sobrecalentamiento"]
        and not estado["ruido"]
        and not estado["lento"]
        and estado["internet"]
        and estado["usb"]
        and estado["audio"]
        and not dano_fisico
    )
    observaciones = tuple(
        (texto, orientacion)
        for clave, valor, texto, orientacion in OBSERVACIONES
        if estado[clave] == valor
    )
    return Evaluacion(
        funcionamiento_basico=p and q and r,
        dano_fisico=dano_fisico,
        respuestas_consistentes=consistentes,
        equipo_correcto=p and q and r and s and sin_fallas_adicionales,
        diagnostico=diagnostico,
        recomendacion=recomendacion,
        observaciones=observaciones,
    )

def generar_reporte(
    datos: dict[str, str],
    estado: dict[str, bool],
    folio: str,
    fecha: datetime,
) -> str:
    evaluacion = evaluar_equipo(estado)
    lineas = [
        "",
        "=" * 60,
        "REPORTE DE DIAGNÓSTICO",
        "=" * 60,
        f"Número de reporte: {folio}",
        f"Fecha: {fecha:%d/%m/%Y}",
        f"Hora: {fecha:%H:%M:%S}",
        "",
        "DATOS DEL USUARIO Y DEL EQUIPO",
    ]
    lineas.extend(f"{etiqueta}: {valor}" for etiqueta, valor in datos.items())
    lineas.extend(["", "ESTADO DEL EQUIPO"])
    lineas.extend(
        f"{etiqueta}: {si_no(estado[clave])}"
        for clave, _, _, etiqueta in PREGUNTAS
    )
    lineas.extend(["", "VALORES DE LAS PROPOSICIONES"])
    lineas.extend(
        f"{simbolo} - {etiqueta}: {estado[clave]}"
        for clave, simbolo, _, etiqueta in PREGUNTAS
        if simbolo
    )
    lineas.extend([
        f"P ∧ Q ∧ R = {evaluacion.funcionamiento_basico}",
        f"Golpe ∨ Agua ∨ Otro daño = {evaluacion.dano_fisico}",
        f"Respuestas consistentes: {si_no(evaluacion.respuestas_consistentes)}",
        "",
        "RESULTADO DEL DIAGNÓSTICO",
        "ESTADO: EQUIPO FUNCIONANDO CORRECTAMENTE"
        if evaluacion.equipo_correcto else "ESTADO: EQUIPO CON FALLAS",
        f"Diagnóstico: {evaluacion.diagnostico}",
    ])
    if evaluacion.recomendacion:
        lineas.append(evaluacion.recomendacion)
    lineas.extend(["", "OBSERVACIONES"])
    for texto, orientacion in evaluacion.observaciones:
        lineas.append(f"- {texto}")
        if orientacion:
            lineas.append(f"  {orientacion}")
    lineas.extend(["", f"Número de reporte: {folio}", "FIN DEL REPORTE"])
    return "\n".join(lineas)

NUMERO = 5
PUERTO = 5105
TITULO = 'Diagnóstico con reporte'
DESCRIPCION = 'Captura los datos del equipo y genera un reporte con folio, fecha, diagnóstico y observaciones.'
GRUPOS = [{'titulo': 'Datos del usuario',
  'campos': [{'clave': 'usuario', 'etiqueta': 'Nombre de usuario', 'tipo': 'texto'},
             {'clave': 'nombre', 'etiqueta': 'Nombre completo', 'tipo': 'texto'},
             {'clave': 'direccion', 'etiqueta': 'Dirección', 'tipo': 'texto'}]},
 {'titulo': 'Datos del equipo',
  'campos': [{'clave': 'modelo', 'etiqueta': 'Modelo', 'tipo': 'texto'},
             {'clave': 'tipo',
              'etiqueta': 'Tipo de equipo',
              'tipo': 'opcion',
              'opciones': {'pc': 'PC',
                           'laptop': 'Laptop',
                           'servidor': 'Servidor',
                           'tablet': 'Tablet'}},
             {'clave': 'antiguedad', 'etiqueta': 'Antigüedad en años', 'tipo': 'numero'},
             {'clave': 'ram', 'etiqueta': 'Memoria RAM en GB', 'tipo': 'numero'},
             {'clave': 'almacenamiento',
              'etiqueta': 'Almacenamiento en GB',
              'tipo': 'numero'},
             {'clave': 'disco',
              'etiqueta': 'Tipo de almacenamiento',
              'tipo': 'opcion',
              'opciones': {'hdd': 'Disco duro HDD',
                           'ssd': 'Disco de estado sólido SSD',
                           'otro': 'Otro tipo de almacenamiento'}},
             {'clave': 'procesador',
              'etiqueta': 'Marca de procesador',
              'tipo': 'opcion',
              'opciones': {'intel': 'Intel', 'amd': 'AMD', 'arm': 'ARM', 'otro': 'Otro'}},
             {'clave': 'sistema_operativo',
              'etiqueta': 'Sistema operativo',
              'tipo': 'texto'},
             {'clave': 'garantia',
              'etiqueta': '¿Tiene garantía vigente?',
              'tipo': 'booleano'},
             {'clave': 'mantenimiento',
              'etiqueta': '¿Ha recibido mantenimiento?',
              'tipo': 'booleano'}]},
 {'titulo': 'Funcionamiento y daños',
  'campos': [{'clave': 'electricidad',
              'etiqueta': '¿El equipo tiene electricidad?',
              'tipo': 'booleano'},
             {'clave': 'enciende',
              'etiqueta': '¿El equipo enciende?',
              'tipo': 'booleano'},
             {'clave': 'imagen',
              'etiqueta': '¿El equipo muestra imagen?',
              'tipo': 'booleano'},
             {'clave': 'sistema_inicia',
              'etiqueta': '¿El sistema operativo inicia correctamente?',
              'tipo': 'booleano'},
             {'clave': 'se_reinicia',
              'etiqueta': '¿El equipo se reinicia o apaga solo?',
              'tipo': 'booleano'},
             {'clave': 'sobrecalentamiento',
              'etiqueta': '¿El equipo se calienta demasiado?',
              'tipo': 'booleano'},
             {'clave': 'ruido',
              'etiqueta': '¿El equipo hace ruidos extraños?',
              'tipo': 'booleano'},
             {'clave': 'lento',
              'etiqueta': '¿El equipo funciona muy lento?',
              'tipo': 'booleano'},
             {'clave': 'internet',
              'etiqueta': '¿El equipo puede conectarse a Internet?',
              'tipo': 'booleano'},
             {'clave': 'usb',
              'etiqueta': '¿Los puertos USB funcionan correctamente?',
              'tipo': 'booleano'},
             {'clave': 'audio',
              'etiqueta': '¿El equipo reproduce sonido correctamente?',
              'tipo': 'booleano'},
             {'clave': 'golpes',
              'etiqueta': '¿El equipo recibió golpes?',
              'tipo': 'booleano'},
             {'clave': 'agua',
              'etiqueta': '¿Al equipo le cayó agua?',
              'tipo': 'booleano'},
             {'clave': 'otro_dano',
              'etiqueta': '¿El equipo tiene algún otro daño visible?',
              'tipo': 'booleano'}]}]
BOTON = 'Generar reporte'


def evaluar(datos):
    informacion = {
        "Usuario": datos["usuario"], "Nombre": datos["nombre"], "Dirección": datos["direccion"],
        "Modelo": datos["modelo"], "Tipo": TIPOS_EQUIPO[datos["tipo"]],
        "Antigüedad": f"{datos['antiguedad']} años", "RAM": f"{datos['ram']} GB",
        "Almacenamiento": f"{datos['almacenamiento']} GB", "Disco": TIPOS_DISCO[datos["disco"]],
        "Procesador": PROCESADORES[datos["procesador"]], "Sistema operativo": datos["sistema_operativo"],
        "Garantía": si_no(datos["garantia"]), "Mantenimiento": si_no(datos["mantenimiento"]),
    }
    estado = {clave: datos[clave] for clave, _, _, _ in PREGUNTAS}
    evaluacion = evaluar_equipo(estado)
    folio = f"REP-{random.randint(1000, 9999)}"
    fecha = datetime.now()
    mensajes = [f"Reporte: {folio} · {fecha:%d/%m/%Y %H:%M:%S}",
                "ESTADO: EQUIPO FUNCIONANDO CORRECTAMENTE" if evaluacion.equipo_correcto else "ESTADO: EQUIPO CON FALLAS"]
    if evaluacion.recomendacion:
        mensajes.append(evaluacion.recomendacion)
    proposiciones = [[f"{simbolo} · {etiqueta}", str(estado[clave])] for clave, simbolo, _, etiqueta in PREGUNTAS if simbolo]
    proposiciones.extend([["P ∧ Q ∧ R", str(evaluacion.funcionamiento_basico)],
                          ["Golpe ∨ Agua ∨ Otro daño", str(evaluacion.dano_fisico)],
                          ["Respuestas consistentes", si_no(evaluacion.respuestas_consistentes)]])
    tablas = [
        {"titulo": "Usuario y equipo", "encabezados": ["Dato", "Valor"], "filas": list(informacion.items())},
        {"titulo": "Estado del equipo", "encabezados": ["Pregunta", "Respuesta"], "filas": [[etiqueta, si_no(estado[clave])] for clave, _, _, etiqueta in PREGUNTAS]},
        {"titulo": "Proposiciones", "encabezados": ["Proposición", "Valor"], "filas": proposiciones},
    ]
    if evaluacion.observaciones:
        tablas.append({"titulo": "Observaciones", "encabezados": ["Observación", "Orientación"], "filas": list(evaluacion.observaciones)})
    return {"titulo": evaluacion.diagnostico, "clase": "positivo" if evaluacion.equipo_correcto else "aviso",
            "mensajes": mensajes, "tablas": tablas, "reporte": generar_reporte(informacion, estado, folio, fecha)}



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
