"""Práctica 6: aplicar las reglas académicas de tres síntomas."""


def pedir_si_no(mensaje: str) -> bool:
    while True:
        respuesta = input(mensaje).strip().casefold()
        if respuesta in ("s", "si", "sí"):
            return True
        if respuesta in ("n", "no"):
            return False
        print("Respuesta inválida. Escribe sí o no (también s o n).")


def evaluar_sintomas(fiebre: bool, tos: bool, dolor_garganta: bool) -> str:
    """Devolver el primer resultado aplicable, con la prioridad original."""
    if fiebre and tos:
        return "Posible infección respiratoria"
    if tos and dolor_garganta:
        return "Posible irritación respiratoria"
    if fiebre:
        return "Se recomienda valoración profesional"
    return "No se identificó un patrón"


def main() -> None:
    print("SISTEMA EXPERTO DE DIAGNÓSTICO")
    fiebre = pedir_si_no("¿Tiene fiebre? (s/n): ")
    tos = pedir_si_no("¿Tiene tos? (s/n): ")
    dolor_garganta = pedir_si_no("¿Tiene dolor de garganta? (s/n): ")

    diagnostico = evaluar_sintomas(fiebre, tos, dolor_garganta)
    print("\nResultado orientativo:")
    print(diagnostico)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nCaptura cancelada. No se emitió un resultado.")
