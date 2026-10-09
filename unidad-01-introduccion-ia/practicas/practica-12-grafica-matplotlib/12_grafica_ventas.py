"""Práctica 12: primer gráfico con Matplotlib.

Materia: Extracción de Conocimiento en Bases de Datos.
Objetivo: representar las ventas simuladas de EcoMart y comparar cada mes
con el promedio anual, conservando los datos del ejercicio del profesor.
"""
import argparse
from pathlib import Path

import matplotlib
import numpy as np


# DATOS: las ventas se expresan en miles de pesos mexicanos.
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
VENTAS = [85, 90, 96, 105, 120, 135, 150, 148, 160, 172, 181, 195]
ANIO = 2026
SALIDA = Path(__file__).resolve().parent / "salidas" / "Grafica_Profesional_01.png"

# Una paleta compartida mantiene consistentes títulos, líneas y anotaciones.
COLORES = {
    "fondo": "#f5f8f7", "texto": "#173d34", "secundario": "#61766f",
    "ventas": "#207f6a", "promedio": "#a86622", "maximo": "#124d40",
    "cuadricula": "#dce6e1",
}


def validar_datos(meses, ventas):
    """Evita longitudes distintas, meses vacíos y valores no representables."""
    if len(meses) != 12:
        raise ValueError("La gráfica anual necesita los doce meses.")
    if any(not isinstance(mes, str) or not mes.strip() for mes in meses):
        raise ValueError("Cada mes debe tener una etiqueta de texto.")
    if len({mes.strip().casefold() for mes in meses}) != 12:
        raise ValueError("Los nombres de los meses no deben repetirse.")
    try:
        valores = np.asarray(ventas, dtype=float)
    except (TypeError, ValueError):
        raise ValueError("Todas las ventas deben ser números.") from None
    if valores.shape != (12,):
        raise ValueError("Debe existir una venta por cada uno de los doce meses.")
    if not np.isfinite(valores).all() or (valores < 0).any():
        raise ValueError("Las ventas deben ser números finitos, mayores o iguales a cero.")
    # También evita desbordamientos al calcular el total o los límites del eje.
    with np.errstate(over="ignore"):
        if not np.isfinite(valores.sum()):
            raise ValueError("Las ventas son demasiado grandes para calcular el total.")
    return valores


def calcular_resumen(valores):
    """El cambio compara diciembre con enero; no es una tasa interanual."""
    crecimiento = None
    if valores[0] > 0:
        crecimiento = (valores[-1] / valores[0] - 1) * 100
    return {
        "total": float(np.sum(valores)),
        "promedio": float(np.mean(valores)),
        "indice_max": int(np.argmax(valores)),
        "crecimiento": crecimiento,
    }


def crear_grafica(meses, ventas):
    """Construye y devuelve la figura; importar el módulo no abre ventanas."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator, StrMethodFormatter

    valores = validar_datos(meses, ventas)
    resumen = calcular_resumen(valores)
    x = np.arange(len(meses))
    indice_max = resumen["indice_max"]
    maximo = valores[indice_max]
    cambio = resumen["crecimiento"]

    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 11}):
        fig, ax = plt.subplots(figsize=(14, 8), facecolor=COLORES["fondo"])
        # Reserva espacio para el encabezado, los indicadores y el pie.
        fig.subplots_adjust(left=0.08, right=0.96, bottom=0.18, top=0.66)
        fig.text(0.08, 0.945, "ECOMART  /  REPORTE DE VENTAS", fontsize=10,
                 weight="bold", color=COLORES["ventas"])
        fig.text(0.08, 0.889, "Ventas mensuales de EcoMart", fontsize=27,
                 weight="bold", color=COLORES["texto"])
        fig.text(0.08, 0.849, f"Enero – diciembre de {ANIO} · Datos simulados",
                 fontsize=12, color=COLORES["secundario"])

        indicadores = [
            ("TOTAL ANUAL", f"{resumen['total']:,.0f}", "miles de pesos"),
            ("PROMEDIO MENSUAL", f"{resumen['promedio']:,.1f}", "miles de pesos"),
            ("CAMBIO ENE → DIC", f"{cambio:+.1f}%" if cambio is not None else "N/D",
             "respecto a enero" if cambio is not None else "enero tiene ventas de cero"),
        ]
        for posicion, (titulo, valor, unidad) in zip((0.08, 0.39, 0.70), indicadores):
            fig.text(posicion, 0.786, titulo, fontsize=9, weight="bold",
                     color=COLORES["secundario"])
            fig.text(posicion, 0.738, valor, fontsize=25, weight="bold",
                     color=COLORES["texto"])
            fig.text(posicion, 0.707, unidad, fontsize=10, color=COLORES["secundario"])

        # GRÁFICA: se usan posiciones numéricas y etiquetas de meses explícitas.
        ax.set_facecolor("white")
        ax.fill_between(x, valores, 0, color=COLORES["ventas"], alpha=0.08)
        ax.plot(x, valores, color=COLORES["ventas"], linewidth=2.8,
                marker="o", markersize=7, markerfacecolor="white",
                markeredgewidth=2, zorder=3, label="Ventas mensuales")
        ax.axhline(resumen["promedio"], color=COLORES["promedio"],
                   linestyle=(0, (5, 4)), linewidth=1.5,
                   label=f"Promedio: {resumen['promedio']:.1f}")
        ax.scatter(x[indice_max], maximo, color=COLORES["maximo"], s=110,
                   edgecolors="white", linewidths=1.5, zorder=4, label="Máximo anual")

        # ANOTACIONES: sus separaciones se expresan en puntos, no en ventas.
        for posicion, venta in zip(x, valores):
            if posicion == indice_max:
                continue  # El máximo ya muestra su valor en la llamada con flecha.
            ax.annotate(f"{venta:g}", (posicion, venta), xytext=(0, 10),
                        textcoords="offset points", ha="center", fontsize=10,
                        color=COLORES["texto"],
                        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1, "alpha": 0.9})
        derecha = indice_max >= len(meses) / 2
        ax.annotate(f"Mayor venta · {meses[indice_max]}\n{maximo:g} mil pesos",
                    xy=(x[indice_max], maximo), xytext=(-24 if derecha else 24, 28),
                    textcoords="offset points", ha="right" if derecha else "left",
                    fontsize=11, weight="bold", color=COLORES["maximo"],
                    bbox={"boxstyle": "round,pad=0.5", "fc": "#eaf3ee", "ec": "none"},
                    arrowprops={"arrowstyle": "->", "color": COLORES["maximo"], "lw": 1.4})

        # EJES Y LEYENDA: el eje vertical parte de cero para conservar la escala.
        ax.set_xticks(x, meses)
        ax.set_xlim(-0.35, len(meses) - 0.65)
        ax.set_ylim(0, max(float(maximo) * 1.30, 1))
        ax.set_xlabel("Mes", labelpad=12, color=COLORES["texto"], weight="bold")
        ax.set_ylabel("Ventas (miles de pesos, MXN)", labelpad=12,
                      color=COLORES["texto"], weight="bold")
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.6g}"))
        ax.set_axisbelow(True)
        ax.grid(axis="y", linestyle="--", linewidth=0.7, color=COLORES["cuadricula"])
        ax.tick_params(axis="both", colors=COLORES["secundario"], length=0, pad=9)
        ax.spines[["top", "right"]].set_visible(False)
        for borde in ("left", "bottom"):
            ax.spines[borde].set_color(COLORES["cuadricula"])
        # Se crea al final para incluir también el promedio y el máximo.
        ax.legend(loc="upper left", ncol=3, frameon=False, fontsize=10,
                  labelcolor=COLORES["texto"])

        conclusion = (f"Mayor venta en {meses[indice_max]}: {maximo:g} mil pesos. "
                      f"Promedio mensual: {resumen['promedio']:.1f} mil pesos.")
        fig.text(0.08, 0.079, conclusion, fontsize=10.5, color=COLORES["texto"])
        fig.text(0.08, 0.036,
                 "Fuente: datos simulados del ejercicio · Elaboración: Einar Ivan Lazcano Luna · UTVT",
                 fontsize=9, color=COLORES["secundario"])
        fig.canvas.manager.set_window_title(f"Práctica 12 · EcoMart {ANIO}")
    return fig, resumen


def main():
    parser = argparse.ArgumentParser(description="Gráfica de ventas mensuales de EcoMart.")
    parser.add_argument("--sin-ventana", action="store_true",
                        help="guardar el PNG sin abrir una ventana gráfica")
    parser.add_argument("--salida", type=Path, default=SALIDA,
                        help="ruta del archivo PNG de salida")
    args = parser.parse_args()
    salida = args.salida.expanduser().resolve()
    if salida.suffix.lower() != ".png":
        parser.error("La ruta de salida debe terminar en .png.")
    if args.sin_ventana:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = None
    try:
        fig, resumen = crear_grafica(MESES, VENTAS)
        salida.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(salida, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
        print("=" * 60)
        print("Gráfica generada correctamente con los 12 meses originales.")
        print(f"Total anual: {resumen['total']:,.0f} mil pesos.")
        print(f"Promedio mensual: {resumen['promedio']:.2f} mil pesos.")
        print(f"Archivo guardado en: {salida}")
        print("=" * 60)
        if not args.sin_ventana:
            if fig.canvas.required_interactive_framework is None:
                print("No hay un entorno gráfico activo. Abre el PNG generado en VS Code.")
            else:
                print("Usa la barra de Matplotlib para acercar, mover o guardar la gráfica.")
                plt.show()
    except (ValueError, OSError) as error:
        parser.exit(1, f"No se pudo generar la gráfica: {error}\n")
    finally:
        if fig is not None:
            plt.close(fig)


if __name__ == "__main__":
    main()
