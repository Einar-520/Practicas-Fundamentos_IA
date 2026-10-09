"""Comparación de las quince paletas del ejemplo graficas3.py del profesor."""
import argparse
from pathlib import Path

import matplotlib
import numpy as np
import seaborn as sns


PALETAS = (
    ("deep", "Categórica"), ("muted", "Categórica"), ("bright", "Categórica"),
    ("pastel", "Categórica"), ("dark", "Categórica"), ("colorblind", "Categórica"),
    ("Blues", "Secuencial"), ("Greens", "Secuencial"), ("Reds", "Secuencial"),
    ("Purples", "Secuencial"), ("viridis", "Secuencial uniforme"),
    ("plasma", "Secuencial uniforme"), ("inferno", "Secuencial uniforme"),
    ("magma", "Secuencial uniforme"), ("cividis", "Secuencial uniforme"),
)
SALIDA = Path(__file__).resolve().parent / "salidas" / "Capitulo03_Paletas_Profesionales.png"


def crear_galeria(semilla=42):
    """Usa los mismos diez valores y la misma escala en todos los paneles."""
    import matplotlib.pyplot as plt

    if not isinstance(semilla, int) or semilla < 0:
        raise ValueError("La semilla debe ser un entero mayor o igual a cero.")
    x = np.arange(1, 11)
    y = np.random.default_rng(semilla).integers(10, 100, size=10)
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 9}):
        fig, axs = plt.subplots(5, 3, figsize=(14, 14), sharex=True, sharey=True,
                                facecolor="#f5f8f7")
        fig.subplots_adjust(left=0.065, right=0.975, top=0.865, bottom=0.095,
                            hspace=0.63, wspace=0.20)
        fig.text(0.065, 0.958, "LABORATORIO DE VISUALIZACIÓN / UTVT", fontsize=10,
                 weight="bold", color="#207f6a")
        fig.text(0.065, 0.918, "Quince paletas, los mismos datos", fontsize=26,
                 weight="bold", color="#173d34")
        fig.text(0.065, 0.889,
                 f"Datos simulados · Semilla {semilla} · Escala común de 0 a 110",
                 fontsize=11, color="#61766f")
        for indice, (ax, (nombre, familia)) in enumerate(zip(axs.flat, PALETAS)):
            colores = sns.color_palette(nombre, n_colors=len(x))
            barras = ax.bar(x, y, color=colores, edgecolor="#53645d", linewidth=0.35)
            ax.bar_label(barras, padding=3, fontsize=7.5, color="#263d34")
            ax.set_title(f"{nombre}  ·  {familia}", loc="left", fontsize=10,
                         weight="bold", pad=12, color="#173d34")
            ax.set_ylim(0, 110)
            ax.set_xticks(x)
            ax.set_yticks([0, 50, 100])
            ax.set_axisbelow(True)
            ax.grid(axis="y", linestyle="--", linewidth=0.6, color="#dce6e1")
            ax.spines[["top", "right"]].set_visible(False)
            for borde in ("left", "bottom"):
                ax.spines[borde].set_color("#cbd8d1")
            ax.tick_params(length=0, colors="#61766f", labelsize=8)
            if indice % 3 == 0:
                ax.set_ylabel("Valor", color="#61766f")
            if indice >= 12:
                ax.set_xlabel("Observación", color="#61766f")
        fig.text(0.065, 0.051,
                 "Se comparan colores por posición; la altura de cada barra representa el valor.",
                 fontsize=10, color="#173d34")
        fig.text(0.065, 0.026,
                 "Fuente: ejemplo graficas3.py · Adaptación: Einar Ivan Lazcano Luna · UTVT",
                 fontsize=9, color="#61766f")
        fig.canvas.manager.set_window_title("Práctica 12 · Paletas de colores")
    return fig, y


def main():
    parser = argparse.ArgumentParser(description="Comparación de paletas con Matplotlib y Seaborn.")
    parser.add_argument("--sin-ventana", action="store_true", help="guardar el PNG sin abrir una ventana")
    parser.add_argument("--semilla", type=int, default=42, help="entero no negativo para repetir los datos")
    parser.add_argument("--salida", type=Path, default=SALIDA, help="ruta del PNG de salida")
    args = parser.parse_args()
    salida = args.salida.expanduser().resolve()
    if salida.suffix.lower() != ".png":
        parser.error("La ruta de salida debe terminar en .png.")
    if args.sin_ventana:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = None
    try:
        fig, valores = crear_galeria(args.semilla)
        salida.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(salida, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
        print("Galería de las 15 paletas generada correctamente.")
        print("Datos utilizados:", ", ".join(map(str, valores)))
        print(f"Archivo guardado en: {salida}")
        if not args.sin_ventana:
            if fig.canvas.required_interactive_framework is None:
                print("No hay un entorno gráfico activo. Abre el PNG generado en VS Code.")
            else:
                plt.show()
    except (ValueError, OSError) as error:
        parser.exit(1, f"No se pudo generar la galería: {error}\n")
    finally:
        if fig is not None:
            plt.close(fig)


if __name__ == "__main__":
    main()
