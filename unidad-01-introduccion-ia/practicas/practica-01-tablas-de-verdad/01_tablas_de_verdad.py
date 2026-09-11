"""Práctica 1: mostrar las operaciones lógicas para cada par de valores."""

from itertools import product


def main() -> None:
    encabezados = ("P", "Q", "¬P", "P∧Q", "P∨Q", "P→Q", "P↔Q")
    ancho = 7
    separador = "=" * (len(encabezados) * ancho)

    print(separador)
    print("TABLAS DE VERDAD")
    print(separador)
    print("".join(f"{titulo:^{ancho}}" for titulo in encabezados))

    # El orden sigue siendo: VV, VF, FV y FF.
    for p, q in product((True, False), repeat=2):
        valores = (p, q, not p, p and q, p or q, (not p) or q, p == q)
        print("".join(f"{str(valor):^{ancho}}" for valor in valores))


if __name__ == "__main__":
    main()
