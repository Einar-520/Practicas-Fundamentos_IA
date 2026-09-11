"""Práctica 7: evaluar siete síntomas y explicar la regla activada."""

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

# El orden equivale al if/elif original: solo se activa la primera coincidencia.
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


def pedir_si_no(mensaje: str) -> bool:
    while True:
        respuesta = input(mensaje).strip().casefold()
        if respuesta in ("s", "si", "sí"):
            return True
        if respuesta in ("n", "no"):
            return False
        print("Respuesta inválida. Escribe sí o no (también s o n).")


def evaluar_sintomas(sintomas: dict[str, bool]) -> Regla:
    """Seleccionar la primera regla cuyos síntomas requeridos estén presentes."""
    for regla in REGLAS:
        if all(sintomas[sintoma] for sintoma in regla.sintomas_requeridos):
            return regla
    return REGLA_POR_DEFECTO


def main() -> None:
    print("SISTEMA EXPERTO DE SALUD MEJORADO")
    print(
        "Este sistema es una práctica académica "
        "y NO sustituye una valoración médica."
    )
    sintomas = {
        sintoma: pedir_si_no(pregunta) for sintoma, pregunta in PREGUNTAS
    }

    regla = evaluar_sintomas(sintomas)
    print("\nREGLA ACTIVADA:", regla.descripcion)
    print("RESULTADO ORIENTATIVO:", regla.diagnostico)
    print("RECOMENDACIÓN:", regla.recomendacion)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nCaptura cancelada. No se emitió un resultado.")
