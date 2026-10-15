"""Gráficas de los resultados; funcionan con Tkinter o sin pantalla."""
from pathlib import Path

from hill_climbing import PRODUCTOS, nombres, numero


AZUL, VERDE, GRIS, NARANJA = "#2368a0", "#16816a", "#a4b0be", "#b45b23"


def preparar_eje(eje):
    eje.set_facecolor("#ffffff")
    eje.spines[["top", "right"]].set_visible(False)
    eje.spines[["left", "bottom"]].set_color("#c8d2dc")
    eje.tick_params(colors="#33475b")
    eje.set_axisbelow(True)
    eje.grid(axis="y", color="#dfe6ed", linestyle="--", linewidth=.7)


def dibujar_lista(eje, resultado):
    preparar_eje(eje)
    posiciones = range(1, len(resultado.valores) + 1)
    eje.plot(posiciones, resultado.valores, "o-", color=GRIS, linewidth=2, label="Lista completa")
    recorrido_x = [i + 1 for i in resultado.indices]
    eje.plot(recorrido_x, resultado.recorrido, "o-", color=AZUL, linewidth=3, markersize=7, label="Recorrido de Hill Climbing")
    for anterior, siguiente in zip(resultado.indices, resultado.indices[1:]):
        eje.annotate("", xy=(siguiente + 1, resultado.valores[siguiente]),
                     xytext=(anterior + 1, resultado.valores[anterior]),
                     arrowprops={"arrowstyle": "->", "color": AZUL, "lw": 2})
    eje.scatter([recorrido_x[-1]], [resultado.valor_final], s=160, color=VERDE, zorder=5, label="Punto de parada")
    for i, valor in enumerate(resultado.valores, 1):
        if len(resultado.valores) <= 15 or i - 1 in (resultado.indices[0], resultado.indices[-1]):
            eje.annotate(numero(valor), (i, valor), xytext=(0, 11), textcoords="offset points", ha="center", fontsize=10)
    if len(resultado.valores) <= 20:
        eje.set_xticks(list(posiciones))
    eje.set_xlabel("Posición en la lista (desde 1)")
    eje.set_ylabel("Valor que se quiere maximizar")
    eje.set_title("1 · Ascender hasta que ningún vecino mejore", loc="left", fontweight="bold", pad=16)
    eje.margins(x=.07, y=.28)
    eje.legend(loc="lower center", fontsize=9, ncol=2)


def dibujar_productos(eje_barras, eje_avance, resultado, verificacion, presupuesto, productos=PRODUCTOS):
    for eje in (eje_barras, eje_avance):
        preparar_eje(eje)
    seleccion = resultado.final
    etiquetas = [f"{p.nombre}\n${p.costo:,}" for p in productos]
    barras = eje_barras.bar(etiquetas, [p.beneficio for p in productos],
                           color=[VERDE if p.nombre in seleccion.productos else GRIS for p in productos], width=.58)
    eje_barras.bar_label(barras, padding=5, fontsize=11)
    eje_barras.set_ylim(0, max(1, max(p.beneficio for p in productos)) * 1.28)
    eje_barras.set_ylabel("Beneficio (unidades)")
    eje_barras.set_xlabel("Producto y costo en pesos · Verde = elegido por Hill Climbing")
    eje_barras.set_title("Productos elegidos: " + nombres(seleccion), loc="left", fontweight="bold", pad=14)
    avances = range(len(resultado.pasos))
    eje_avance.plot(avances, [s.beneficio for s in resultado.pasos], "o-", color=AZUL, linewidth=2.8,
                    label="Hill Climbing")
    eje_avance.axhline(verificacion.beneficio, color=NARANJA, linestyle="--", linewidth=1.6,
                      label=f"Óptimo global verificado: {verificacion.beneficio}")
    for i, seleccion_paso in enumerate(resultado.pasos):
        eje_avance.annotate(str(seleccion_paso.beneficio), (i, seleccion_paso.beneficio),
                           xytext=(0, 10), textcoords="offset points", ha="center", fontsize=10)
    eje_avance.set_xticks(list(avances), ["Inicio" if i == 0 else f"Paso {i}" for i in avances])
    eje_avance.set_ylabel("Beneficio acumulado (unidades)")
    eje_avance.set_ylim(-max(5, verificacion.beneficio * .06), max(10, verificacion.beneficio * 1.3))
    eje_avance.set_title(f"Costo ${seleccion.costo:,} / ${presupuesto:,} · Disponible ${presupuesto - seleccion.costo:,}",
                        loc="left", fontsize=11, pad=14)
    eje_avance.margins(x=.12)
    eje_avance.legend(loc="lower right", fontsize=9)


def actualizar_lista(figura, resultado):
    figura.clear()
    dibujar_lista(figura.add_subplot(), resultado)


def actualizar_productos(figura, resultado, verificacion, presupuesto):
    figura.clear()
    ejes = figura.subplots(2, 1)
    dibujar_productos(*ejes, resultado, verificacion, presupuesto)


def guardar_png(destino, lista, resultado, verificacion, presupuesto):
    """Exporta los dos ejercicios a una imagen independiente de la ventana."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    destino = Path(destino).expanduser().resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    figura = Figure(figsize=(14, 10), dpi=180, layout="constrained", facecolor="#f5f8fc")
    FigureCanvasAgg(figura)
    rejilla = figura.add_gridspec(2, 2)
    dibujar_lista(figura.add_subplot(rejilla[0, :]), lista)
    dibujar_productos(figura.add_subplot(rejilla[1, 0]), figura.add_subplot(rejilla[1, 1]),
                      resultado, verificacion, presupuesto)
    texto = ("Coincide con el óptimo global." if resultado.final.beneficio == verificacion.beneficio
             else f"Máximo local: faltan {verificacion.beneficio - resultado.final.beneficio} unidades para el óptimo global.")
    figura.suptitle("PRÁCTICA 17 · HILL CLIMBING\n"
                    f"Beneficio encontrado: {resultado.final.beneficio} unidades · {texto}",
                    fontsize=17, fontweight="bold", color="#20354e")
    figura.supxlabel(f"Una unidad por producto · Comprobación independiente: {verificacion.combinaciones} combinaciones · UTVT",
                     fontsize=10, color="#52647a")
    figura.savefig(destino, format="png", dpi=180)
    return destino
