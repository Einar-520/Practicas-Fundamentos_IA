"""Práctica 4: evaluar el funcionamiento y los daños físicos del equipo."""

TIPOS_EQUIPO = ("pc", "laptop", "servidor", "tablet")


def pedir_texto(mensaje: str) -> str:
    while True:
        texto = input(mensaje).strip()
        if texto:
            return texto
        print("Este dato no puede quedar vacío.")


def pedir_tipo_equipo() -> str:
    opciones = "/".join(TIPOS_EQUIPO)
    while True:
        tipo = input(f"¿Qué tipo de equipo es? ({opciones}): ").strip().casefold()
        if tipo in TIPOS_EQUIPO:
            return tipo
        print(f"Tipo inválido. Elige una de estas opciones: {opciones}.")


def pedir_si_no(mensaje: str) -> bool:
    while True:
        respuesta = input(mensaje).strip().casefold()
        if respuesta in ("s", "si", "sí"):
            return True
        if respuesta in ("n", "no"):
            return False
        print("Respuesta inválida. Escribe sí o no (también s o n).")


def diagnosticar_equipo(electricidad: bool, enciende: bool, imagen: bool) -> str:
    """Aplicar la primera condición que corresponda, en el orden original."""
    if not electricidad:
        return "El equipo NO recibe electricidad."
    if not enciende:
        return "El equipo tiene electricidad, pero NO enciende."
    if not imagen:
        return "El equipo enciende, pero NO muestra imagen."
    return "El equipo funciona correctamente."


def main() -> None:
    print("DIAGNÓSTICO DE EQUIPO DE CÓMPUTO")
    modelo = pedir_texto("¿Cuál es el modelo del equipo?: ")
    tipo_equipo = pedir_tipo_equipo()
    electricidad = pedir_si_no("¿El equipo tiene electricidad? (si/no): ")
    enciende = pedir_si_no("¿El equipo enciende? (si/no): ")
    imagen = pedir_si_no("¿El equipo muestra imagen? (si/no): ")
    golpes = pedir_si_no("¿El equipo recibió golpes? (si/no): ")
    agua = pedir_si_no("¿Al equipo le cayó agua? (si/no): ")
    otro_dano = pedir_si_no("¿Tiene otro daño visible? (si/no): ")

    print(f"\nEquipo: {modelo} ({tipo_equipo})")
    print(diagnosticar_equipo(electricidad, enciende, imagen))
    if golpes or agua or otro_dano:
        print("También se detectó daño físico.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nCaptura cancelada. No se emitió un resultado.")
