"""Práctica 5: diagnóstico con reporte, recuperado del proyecto original."""

import random
from dataclasses import dataclass
from datetime import datetime
from math import isfinite

TIPOS_EQUIPO = {"pc": "PC", "laptop": "Laptop", "servidor": "Servidor", "tablet": "Tablet"}
TIPOS_DISCO = {
    "hdd": "Disco duro HDD",
    "ssd": "Disco de estado sólido SSD",
    "otro": "Otro tipo de almacenamiento",
}
PROCESADORES = {"intel": "Intel", "amd": "AMD", "arm": "ARM", "otro": "Otro"}

# Clave, símbolo proposicional, pregunta y etiqueta del reporte.
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

# Cada observación mantiene la condición y la orientación del código recibido.
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


def pedir_texto(mensaje: str) -> str:
    while True:
        valor = input(mensaje).strip()
        if valor:
            return valor
        print("Este dato no puede quedar vacío.")


def pedir_numero(mensaje: str) -> float:
    while True:
        try:
            valor = float(input(mensaje).strip())
        except ValueError:
            print("Ingresa un número válido. Usa punto para los decimales.")
            continue
        if isfinite(valor):
            return valor
        print("Ingresa un número finito; no se aceptan NaN ni infinito.")


def pedir_si_no(mensaje: str) -> bool:
    while True:
        valor = input(mensaje).strip().casefold()
        if valor in ("s", "si", "sí"):
            return True
        if valor in ("n", "no"):
            return False
        print("Respuesta inválida. Escribe sí o no (también s o n).")


def pedir_opcion(mensaje: str, opciones: dict[str, str]) -> str:
    while True:
        valor = input(f"{mensaje} ({'/'.join(opciones)}): ").strip().casefold()
        if valor in opciones:
            return opciones[valor]
        print("Opción inválida. Elige una de las opciones indicadas.")


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


def main() -> None:
    print("BIENVENIDO AL SISTEMA DE DIAGNÓSTICO DE EQUIPOS")
    folio = f"REP-{random.randint(1000, 9999)}"
    fecha = datetime.now()
    print("Número de reporte generado:", folio)

    datos = {
        "Usuario": pedir_texto("Crea un nombre de usuario: "),
        "Nombre": pedir_texto("Ingresa tu nombre completo: "),
        "Dirección": pedir_texto("Ingresa tu dirección: "),
        "Modelo": pedir_texto("¿Cuál es el modelo del equipo?: "),
        "Tipo": pedir_opcion("¿Qué tipo de equipo es?", TIPOS_EQUIPO),
        "Antigüedad": f"{pedir_numero('¿Cuántos años de antigüedad tiene el equipo?: ')} años",
        "RAM": f"{pedir_numero('¿Cuántos GB de RAM tiene el equipo?: ')} GB",
        "Almacenamiento": f"{pedir_numero('¿Cuántos GB de almacenamiento tiene el equipo?: ')} GB",
        "Disco": pedir_opcion("¿Qué tipo de almacenamiento tiene?", TIPOS_DISCO),
        "Procesador": pedir_opcion("¿Cuál es la marca del procesador?", PROCESADORES),
        "Sistema operativo": pedir_texto("¿Qué sistema operativo tiene instalado?: "),
        "Garantía": si_no(pedir_si_no("¿El equipo tiene garantía vigente? (si/no): ")),
        "Mantenimiento": si_no(pedir_si_no("¿El equipo ha recibido mantenimiento previamente? (si/no): ")),
    }
    estado = {
        clave: pedir_si_no(f"{pregunta} (si/no): ")
        for clave, _, pregunta, _ in PREGUNTAS
    }
    print(generar_reporte(datos, estado, folio, fecha))


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nCaptura cancelada. No se emitió un reporte.")
