"""Práctica 19: elegir, colorear, mostrar y exportar 24 gráficas."""
import argparse
from pathlib import Path


CARPETA_SALIDA = Path(__file__).resolve().parent / "salida_graficas"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listar", action="store_true", help="mostrar los 24 tipos y su propósito")
    parser.add_argument("--grafica", type=int, choices=range(1, 25), nargs="+", metavar="1..24",
                        help="números de las gráficas; por defecto genera todas")
    parser.add_argument("--paleta", choices=("original", "oceano", "tierra"), default="original")
    parser.add_argument("--salida", type=Path, default=CARPETA_SALIDA, help="carpeta para los PNG")
    parser.add_argument("--dpi", type=int, default=180, help="resolución entre 72 y 600 dpi")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--mostrar", action="store_true", help="abrir cada gráfica; cerrar para continuar")
    modo.add_argument("--sin-ventana", action="store_true", help="solo exportar PNG (comportamiento predeterminado)")
    args = parser.parse_args(argv)
    if not 72 <= args.dpi <= 600:
        parser.error("La resolución debe estar entre 72 y 600 dpi.")
    try:
        import matplotlib
        if not args.mostrar:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from datos import generar_datos
        from paletas import PALETAS, estilo
        from graficas import CATALOGO
    except ImportError:
        parser.exit(1, "Instala las dependencias: python3 -m pip install -r requirements.txt\n")
    if args.listar:
        for numero, (_, titulo, uso, _) in CATALOGO.items():
            print(f"{numero:02} · {titulo}: {uso}")
        return
    if args.mostrar and str(matplotlib.get_backend()).lower() in {"agg", "pdf", "svg", "ps", "cairo", "template"}:
        parser.exit(1, "No se detectó una ventana gráfica. Revisa Tkinter y WSLg, o ejecuta con --sin-ventana.\n")
    numeros = list(dict.fromkeys(args.grafica or CATALOGO))
    paleta = PALETAS[args.paleta]
    datos = generar_datos()
    destino = args.salida.expanduser().resolve() / args.paleta
    try:
        destino.mkdir(parents=True, exist_ok=True)
        with plt.rc_context(estilo(paleta)):
            for numero in numeros:
                nombre, titulo, _, dibujar = CATALOGO[numero]
                figura = dibujar(datos, paleta)
                try:
                    figura.text(.01, .012, f"PRÁCTICA 19 · Datos ficticios · Paleta: {args.paleta}",
                                fontsize=8, color="#64748B")
                    figura.tight_layout(rect=(0, .04, 1, 1))
                    ruta = destino / f"{nombre}.png"
                    figura.savefig(ruta, dpi=args.dpi, bbox_inches="tight", facecolor="white")
                    print(f"{numero:02} · {titulo}\n   Guardada: {ruta}")
                    if args.mostrar:
                        plt.show(block=True)
                finally:
                    plt.close(figura)
        print(f"\nListo: {len(numeros)} gráficas generadas con la paleta {args.paleta}.")
    except (OSError, ValueError) as error:
        parser.exit(1, f"No se pudo generar el catálogo: {error}\n")


if __name__ == "__main__":
    main()
