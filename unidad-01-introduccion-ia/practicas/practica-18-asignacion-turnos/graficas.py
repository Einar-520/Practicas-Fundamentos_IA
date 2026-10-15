"""Representación de la satisfacción sin confundir preferencias con horarios."""
from pathlib import Path

from asignacion import EMPLEADOS, PREFERENCIAS, puntuar, validar_asignacion


def dibujar(figura, asignacion, resultado, verificacion):
    asignacion = validar_asignacion(asignacion)
    figura.clear()
    barras, avance = figura.subplots(1, 2)
    satisfechos = [int(t == p) for t, p in zip(asignacion, PREFERENCIAS)]
    barras.bar(range(4), satisfechos, color=["#17836c" if valor else "#b75f2c" for valor in satisfechos], width=.6)
    barras.set_xticks(range(4), [f"{nombre}\n{turno}" for nombre, turno in zip(EMPLEADOS, asignacion)], fontsize=9)
    for i, valor in enumerate(satisfechos):
        if not valor:
            barras.plot(i, 0, "o", color="#b75f2c", markersize=7)
        barras.annotate("Sí" if valor else "No", (i, valor), xytext=(0, 8),
                        textcoords="offset points", ha="center", fontweight="bold")
    barras.set_yticks([0, 1], ["0 · No", "1 · Sí"])
    barras.set_ylim(-.12, 1.35)
    barras.set_title("¿Cumple su preferencia?", loc="left", fontweight="bold", pad=14)
    barras.set_xlabel("Empleado y turno de la asignación mostrada", fontsize=9)
    pasos = range(len(resultado.pasos))
    avance.plot(pasos, [p.satisfaccion for p in resultado.pasos], "o-", color="#286ba6", linewidth=2.5, label="Hill Climbing")
    avance.axhline(verificacion.satisfaccion, color="#b75f2c", linestyle="--", label=f"Óptimo comprobado: {verificacion.satisfaccion}")
    for i, paso in enumerate(resultado.pasos):
        avance.annotate(str(paso.satisfaccion), (i, paso.satisfaccion), xytext=(0, 10), textcoords="offset points", ha="center")
    avance.set_xticks(list(pasos), ["Inicio" if i == 0 else f"Paso {i}" for i in pasos])
    avance.set_yticks(range(5))
    avance.set_ylim(-.25, 4.25)
    avance.margins(x=.15)
    avance.set_ylabel("Preferencias cumplidas")
    avance.set_title("Avance de la búsqueda", loc="left", fontweight="bold", pad=14)
    avance.legend(loc="lower right", fontsize=9)
    for eje in (barras, avance):
        eje.spines[["top", "right"]].set_visible(False)
        eje.spines[["left", "bottom"]].set_color("#b9c7d5")
        eje.set_axisbelow(True)
        eje.grid(axis="y", linestyle="--", color="#dce4ec", linewidth=.7)
        eje.tick_params(colors="#34495e")


def guardar_png(destino, asignacion, resultado, verificacion):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    destino = Path(destino).expanduser().resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    figura = Figure(figsize=(13, 6.5), dpi=180, layout="constrained", facecolor="#f5f8fc")
    FigureCanvasAgg(figura)
    dibujar(figura, asignacion, resultado, verificacion)
    puntos = puntuar(asignacion)
    figura.suptitle(f"PRÁCTICA 18 · ASIGNACIÓN DE TURNOS\n{puntos} de 4 preferencias cumplidas · Satisfacción {puntos / 4:.0%}",
                    fontweight="bold", fontsize=18, color="#20354e")
    figura.supxlabel("Un empleado por turno · Un punto por preferencia cumplida · Verificación de 24 asignaciones · UTVT",
                     fontsize=10, color="#52647a")
    figura.savefig(destino, dpi=180, format="png")
    return destino
