"""Práctica 2: autorizar un examen con las condiciones originales."""

from math import isfinite

ASISTENCIA_MINIMA = 80
PROMEDIO_MINIMO = 8


def pedir_numero(mensaje: str) -> float:
    """Repetir la pregunta hasta recibir un número finito."""
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
        respuesta = input(mensaje).strip().casefold()
        if respuesta in ("s", "si", "sí"):
            return True
        if respuesta in ("n", "no"):
            return False
        print("Respuesta inválida. Escribe sí o no (también s o n).")


def puede_presentar_examen(
    asistencia: float,
    promedio: float,
    proyecto: bool,
    adeudos: bool,
    autorizacion: bool,
) -> bool:
    cumple_asistencia = asistencia >= ASISTENCIA_MINIMA  # P
    cumple_promedio = promedio >= PROMEDIO_MINIMO  # Q
    sin_adeudos = not adeudos  # S; proyecto es R y autorización es T.

    # Regla original: (P ∧ Q ∧ R ∧ S) ∨ T.
    return (
        cumple_asistencia and cumple_promedio and proyecto and sin_adeudos
    ) or autorizacion


def main() -> None:
    print("SISTEMA DE AUTORIZACIÓN PARA EXAMEN")
    asistencia = pedir_numero("Ingresa el porcentaje de asistencia: ")
    promedio = pedir_numero("Ingresa el promedio: ")
    proyecto = pedir_si_no("¿Entregó el proyecto? (si/no): ")
    adeudos = pedir_si_no("¿Tiene adeudos? (si/no): ")
    autorizacion = pedir_si_no("¿Tiene autorización especial? (si/no): ")

    resultado = puede_presentar_examen(
        asistencia, promedio, proyecto, adeudos, autorizacion
    )
    if resultado:
        print("El alumno PUEDE presentar el examen.")
    else:
        print("El alumno NO puede presentar el examen.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nCaptura cancelada. No se emitió un resultado.")
