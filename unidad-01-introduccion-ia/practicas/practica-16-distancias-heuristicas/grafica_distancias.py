"""Una misma escala en ambos ejes permite comparar las dos longitudes."""
from pathlib import Path

from distancias import conclusion, numero, ruta_manhattan, texto_punto


COLOR_MANHATTAN = "#dc752b"
COLOR_EUCLIDIANA = "#236db5"
LIMITE_GRAFICO = 1_000_000


def validar_rango_grafico(medicion):
    # El límite pertenece al visor, no a las fórmulas de distancia.
    if any(abs(v) > LIMITE_GRAFICO for p in (medicion.a, medicion.b) for v in p):
        raise ValueError("Para dibujar, usa coordenadas entre -1000000 y 1000000.")


def dibujar_comparacion(figura, medicion, orden="xy"):
    from matplotlib.ticker import MaxNLocator

    validar_rango_grafico(medicion)
    ruta = ruta_manhattan(medicion, orden)
    figura.clear()
    figura.set_facecolor("#f5f8fc")
    ax = figura.add_subplot()
    ax.set_facecolor("white")
    ax.set_title(f"A {texto_punto(medicion.a)}  →  B {texto_punto(medicion.b)}",
                 loc="left", fontsize=15, fontweight="bold", color="#20354e", pad=16)
    # La línea gruesa queda debajo de la discontinua; así ambas se distinguen
    # cuando los puntos están alineados y las dos rutas se superponen.
    ax.plot([p[0] for p in ruta], [p[1] for p in ruta], color=COLOR_MANHATTAN,
            linewidth=4.5, solid_capstyle="round", zorder=3, gid="manhattan",
            label=f"Manhattan: {numero(medicion.manhattan)} unidades")
    ax.plot([medicion.a[0], medicion.b[0]], [medicion.a[1], medicion.b[1]],
            color=COLOR_EUCLIDIANA, linewidth=2.6, linestyle="--", zorder=4,
            gid="euclidiana", label=f"Euclidiana: {numero(medicion.euclidiana)} unidades")

    if medicion.a == medicion.b:
        ax.scatter(*medicion.a, s=115, color="#20354e", zorder=5)
        ax.annotate(f"A = B {texto_punto(medicion.a)}", medicion.a,
                    xytext=(10, 12), textcoords="offset points", fontsize=11, weight="bold")
    else:
        ax.scatter([medicion.a[0], medicion.b[0]], [medicion.a[1], medicion.b[1]],
                   s=105, color=["#24785b", "#20354e"], edgecolors="white", linewidths=1.5, zorder=5)
        for nombre, punto in (("A", medicion.a), ("B", medicion.b)):
            otro = medicion.b if nombre == "A" else medicion.a
            izquierda = otro[0] >= punto[0]
            ax.annotate(f"{nombre} {texto_punto(punto)}", punto, xytext=(-10 if izquierda else 10, 12),
                        ha="right" if izquierda else "left", textcoords="offset points",
                        fontsize=11, weight="bold", color="#20354e")
        if medicion.dx and medicion.dy:
            for inicio, final in zip(ruta, ruta[1:]):
                horizontal = inicio[1] == final[1]
                texto = f"Δx = {numero(medicion.dx)}" if horizontal else f"Δy = {numero(medicion.dy)}"
                centro = ((inicio[0] + final[0]) / 2, (inicio[1] + final[1]) / 2)
                ax.annotate(texto, centro, xytext=(0, -20) if horizontal else (12, 0),
                            textcoords="offset points", ha="center" if horizontal else "left",
                            va="center", fontsize=10, color="#a75416",
                            bbox={"facecolor": "white", "edgecolor": "none", "alpha": .9, "pad": 2})

    amplitud = max(medicion.dx, medicion.dy, 2.0)
    semilado = amplitud * .73
    centro_x = (medicion.a[0] + medicion.b[0]) / 2
    centro_y = (medicion.a[1] + medicion.b[1]) / 2
    ax.set_xlim(centro_x - semilado, centro_x + semilado)
    ax.set_ylim(centro_y - semilado, centro_y + semilado)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Coordenada X (unidades)", labelpad=10, color="#20354e")
    ax.set_ylabel("Coordenada Y (unidades)", labelpad=10, color="#20354e")
    for eje in (ax.xaxis, ax.yaxis):
        eje.set_major_locator(MaxNLocator(nbins=8, steps=[1, 2, 5, 10]))
    ax.ticklabel_format(useOffset=False, style="plain")
    ax.grid(color="#dbe4ef", linestyle=":", linewidth=.9)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#b4c2d3")
    ax.legend(loc="upper left", framealpha=.96, facecolor="white", edgecolor="#dbe4ef", fontsize=10)
    figura.supxlabel(conclusion(medicion), fontsize=10, color="#405c78")
    return ax


def crear_figura(medicion, orden="xy"):
    from matplotlib.figure import Figure
    figura = Figure(figsize=(9, 7), dpi=100, layout="constrained")
    dibujar_comparacion(figura, medicion, orden)
    return figura


def guardar_png(medicion, destino, orden="xy"):
    """Exporta la misma comparación sin necesitar Tkinter ni una pantalla."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    figura = crear_figura(medicion, orden)
    FigureCanvasAgg(figura)
    ruta = Path(destino).expanduser()
    if ruta.suffix.lower() != ".png":
        raise ValueError("El archivo de salida debe tener extensión .png.")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(ruta, dpi=180, facecolor=figura.get_facecolor())
    return ruta.resolve()
