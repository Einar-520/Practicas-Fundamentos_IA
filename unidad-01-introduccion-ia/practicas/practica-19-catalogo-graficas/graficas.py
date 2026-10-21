"""Veinticuatro ejemplos independientes de Matplotlib, basados en graficas.py.
Cada función recibe los datos y la paleta, y devuelve una figura sin guardarla.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from datos import Datos
from paletas import Paleta, color_texto


def malla_funcion():
    x = np.linspace(-3, 3, 100)
    X, Y = np.meshgrid(x, x)
    return X, Y, np.sin(np.sqrt(X**2 + Y**2))


def grafica_lineas(d: Datos, p: Paleta):
    """Observar tendencias a través del tiempo."""
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        d.meses,
        d.ventas,
        color=p.principal,
        marker="o",
        linewidth=2.5,
        label="Ventas"
    )

    ax.set_title("Evolución mensual de ventas")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Ventas (miles de pesos)")
    ax.grid(axis="y")
    ax.legend()
    return fig


def grafica_lineas_multiples(d: Datos, p: Paleta):
    """Comparar varias series a través del tiempo."""
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(d.meses, d.ventas, marker="o",
            color=p.principal, label="Ventas")

    ax.plot(d.meses, d.costos, marker="s",
            color=p.acento, label="Costos")

    ax.plot(d.meses, d.utilidad, marker="^",
            color=p.secundario, label="Utilidad")

    ax.set_title("Comparación de ventas, costos y utilidad")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Importe (miles de pesos)")
    ax.grid(axis="y")
    ax.legend()
    return fig


def grafica_barras_verticales(d: Datos, p: Paleta):
    """Comparar categorías."""
    fig, ax = plt.subplots(figsize=(9, 5))

    barras = ax.bar(
        d.productos,
        d.ventas_productos,
        color=p.categorias[:len(d.productos)]
    )

    ax.bar_label(barras, padding=3, fmt="%.0f")
    ax.set_title("Ventas por producto")
    ax.set_xlabel("Producto")
    ax.set_ylabel("Unidades vendidas")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.margins(y=0.15)
    return fig


def grafica_barras_horizontales(d: Datos, p: Paleta):
    """Categorías con nombres largos."""
    fig, ax = plt.subplots(figsize=(9, 5))

    orden = np.argsort(-np.asarray(d.ventas_productos))

    barras = ax.barh(
        [d.productos[i] for i in orden],
        [d.ventas_productos[i] for i in orden],
        color=[p.categorias[i] for i in orden]
    )

    ax.bar_label(barras, padding=4)
    ax.set_title("Ranking de ventas por producto")
    ax.set_xlabel("Unidades vendidas")
    ax.set_ylabel("Producto")
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.invert_yaxis()
    ax.margins(x=0.15)
    return fig


def grafica_barras_agrupadas(d: Datos, p: Paleta):
    """Comparar dos o más grupos por categoría."""
    ventas_2025 = np.array([100, 120, 150, 130, 170])
    ventas_2026 = np.array([115, 135, 160, 145, 190])

    x = np.arange(len(d.productos))
    ancho = 0.38

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar(
        x - ancho / 2,
        ventas_2025,
        ancho,
        label="2025",
        color=p.principal
    )

    ax.bar(
        x + ancho / 2,
        ventas_2026,
        ancho,
        label="2026",
        color=p.acento
    )

    ax.set_xticks(x)
    ax.set_xticklabels(d.productos)
    ax.set_title("Comparación de ventas por año")
    ax.set_ylabel("Unidades")
    ax.legend()
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.margins(y=0.15)
    return fig


def grafica_barras_apiladas(d: Datos, p: Paleta):
    """Mostrar componentes de un total."""
    ventas_online = np.array([40, 50, 55, 60, 70])
    ventas_tienda = np.array([60, 70, 80, 70, 100])

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(
        d.productos,
        ventas_online,
        label="Ventas en línea",
        color=p.principal
    )

    ax.bar(
        d.productos,
        ventas_tienda,
        bottom=ventas_online,
        label="Ventas en tienda",
        color=p.secundario
    )

    ax.set_title("Ventas por canal")
    ax.set_ylabel("Unidades")
    ax.legend()
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.margins(y=0.15)
    return fig


def grafica_area(d: Datos, p: Paleta):
    """Destacar la magnitud mensual; no representa un acumulado."""
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.fill_between(
        d.meses,
        d.ventas,
        color=p.principal,
        alpha=0.22
    )

    ax.plot(
        d.meses,
        d.ventas,
        color=p.principal,
        linewidth=2.5,
        marker="o"
    )

    ax.set_title("Área de ventas mensuales")
    ax.set_ylabel("Ventas (miles de pesos)")
    ax.grid(axis="y")
    ax.set_xlabel("Mes")
    ax.set_ylim(bottom=0)
    return fig


def grafica_areas_apiladas(d: Datos, p: Paleta):
    """Comparar la composición de varias series."""
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.stackplot(
        d.meses,
        d.costos,
        d.utilidad,
        labels=["Costos", "Utilidad"],
        colors=[p.acento, p.secundario],
        alpha=0.85
    )

    ax.set_title("Composición de las ventas")
    ax.set_ylabel("Importe (miles de pesos)")
    ax.legend(loc="upper left")
    ax.grid(axis="y")
    ax.set_xlabel("Mes")
    return fig


def grafica_pastel(d: Datos, p: Paleta):
    """Mostrar proporciones de un total."""
    fig, ax = plt.subplots(figsize=(7, 7))

    sectores, etiquetas, porcentajes = ax.pie(
        d.participacion,
        labels=d.categorias,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.67,
        colors=p.categorias[:len(d.categorias)],
        wedgeprops={"edgecolor": "white", "linewidth": 2}
    )

    ax.set_title("Participación por categoría")
    ax.axis("equal")
    for sector, etiqueta in zip(sectores, porcentajes):
        etiqueta.set_color(color_texto(sector.get_facecolor()))
        etiqueta.set_weight("bold")
    return fig


def grafica_dona(d: Datos, p: Paleta):
    """Proporciones con un espacio central para destacar un indicador o texto."""
    fig, ax = plt.subplots(figsize=(7, 7))

    sectores, etiquetas, porcentajes = ax.pie(
        d.participacion,
        labels=d.categorias,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.79,
        colors=p.categorias[:len(d.categorias)],
        wedgeprops={"width": 0.42, "edgecolor": "white"}
    )

    ax.text(
        0, 0,
        "Participación\npor categoría",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold"
    )

    ax.set_title("Distribución de categorías")
    ax.axis("equal")
    for sector, etiqueta in zip(sectores, porcentajes):
        etiqueta.set_color(color_texto(sector.get_facecolor()))
        etiqueta.set_weight("bold")
    return fig


def grafica_histograma(d: Datos, p: Paleta):
    """Observar la distribución de una variable numérica."""
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.hist(
        d.calificaciones,
        bins=15,
        color=p.principal,
        edgecolor="white",
        alpha=0.9
    )

    ax.axvline(
        np.mean(d.calificaciones),
        color=p.alerta,
        linestyle="--",
        linewidth=2,
        label=f"Media: {np.mean(d.calificaciones):.1f}"
    )

    ax.set_title("Distribución de calificaciones")
    ax.set_xlabel("Calificación")
    ax.set_ylabel("Frecuencia")
    ax.legend()
    ax.grid(axis="y")
    return fig


def grafica_caja_bigotes(d: Datos, p: Paleta):
    """Comparar medianas, dispersión y posibles valores atípicos entre grupos."""
    fig, ax = plt.subplots(figsize=(8, 5))

    cajas = ax.boxplot(
        [d.grupo_a, d.grupo_b, d.grupo_c],
        tick_labels=["Grupo A", "Grupo B", "Grupo C"],
        patch_artist=True,
        showmeans=True,
        medianprops={"color": "#1E293B", "linewidth": 1.7},
        meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "#1E293B"}
    )

    for caja, color in zip(cajas["boxes"], p.categorias[:3]):
        caja.set_facecolor(color)
        caja.set_alpha(0.65)

    ax.set_title("Distribución de calificaciones por grupo")
    ax.set_ylabel("Calificación")
    ax.grid(axis="y")
    ax.legend(handles=[Line2D([], [], color="#1E293B", label="Mediana"),
                       Line2D([], [], linestyle="", marker="D", markerfacecolor="white",
                              markeredgecolor="#1E293B", label="Media")], fontsize=9)
    return fig


def grafica_violin(d: Datos, p: Paleta):
    """Observar la forma de la distribución de cada grupo."""
    fig, ax = plt.subplots(figsize=(8, 5))

    violines = ax.violinplot(
        [d.grupo_a, d.grupo_b, d.grupo_c],
        showmeans=True,
        showmedians=True
    )

    for cuerpo, color in zip(violines["bodies"], p.categorias[:3]):
        cuerpo.set_facecolor(color)
        cuerpo.set_alpha(0.65)

    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(["Grupo A", "Grupo B", "Grupo C"])
    ax.set_title("Distribución estadística por grupo")
    ax.set_ylabel("Calificación")
    ax.grid(axis="y")
    violines["cmeans"].set_color("#1E293B")
    violines["cmedians"].set_color("#1E293B")
    violines["cmedians"].set_linestyle("--")
    ax.legend(handles=[Line2D([], [], color="#1E293B", label="Media"),
                       Line2D([], [], color="#1E293B", linestyle="--", label="Mediana")], fontsize=9)
    return fig


def grafica_dispersion(d: Datos, p: Paleta):
    """Investigar la relación entre dos variables."""
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.scatter(
        d.horas_estudio,
        d.notas,
        color=p.principal,
        alpha=0.7,
        edgecolors="white",
        s=55
    )

    ax.set_title("Horas de estudio frente a calificación")
    ax.set_xlabel("Horas de estudio")
    ax.set_ylabel("Calificación")
    ax.grid(True)
    return fig


def grafica_burbujas(d: Datos, p: Paleta):
    """Representar tres variables numéricas. x e y son posiciones; el tamaño representa una tercera variable."""
    rng_burbujas = np.random.default_rng(7)

    x_burbujas = rng_burbujas.uniform(1, 10, 35)
    y_burbujas = rng_burbujas.uniform(10, 100, 35)
    tamano = rng_burbujas.uniform(30, 400, 35)

    fig, ax = plt.subplots(figsize=(8, 5))

    puntos = ax.scatter(
        x_burbujas,
        y_burbujas,
        s=tamano,
        c=tamano,
        cmap=p.secuencial,
        alpha=0.65,
        edgecolors="white"
    )

    fig.colorbar(puntos, ax=ax, label="Magnitud representada")

    ax.set_title("Gráfica de burbujas")
    ax.set_xlabel("Variable X")
    ax.set_ylabel("Variable Y")
    ax.grid(True)
    return fig


def grafica_mapa_calor(d: Datos, p: Paleta):
    """Observar relaciones lineales entre variables."""
    datos = np.column_stack([
        d.horas_estudio,
        d.notas,
        d.variable_adicional
    ])

    nombres_variables = [
        "Horas de estudio",
        "Calificación",
        "Variable adicional"
    ]

    matriz_corr = np.corrcoef(datos, rowvar=False)

    fig, ax = plt.subplots(figsize=(7, 6))

    imagen = ax.imshow(
        matriz_corr,
        cmap=p.divergente,
        vmin=-1,
        vmax=1
    )

    fig.colorbar(imagen, ax=ax, label="Correlación")

    ax.set_xticks(range(len(nombres_variables)))
    ax.set_yticks(range(len(nombres_variables)))
    ax.set_xticklabels(nombres_variables, rotation=25, ha="right")
    ax.set_yticklabels(nombres_variables)

    for fila in range(len(nombres_variables)):
        for columna in range(len(nombres_variables)):
            ax.text(
                columna,
                fila,
                f"{matriz_corr[fila, columna]:.2f}",
                ha="center",
                va="center",
                color=color_texto(imagen.cmap(imagen.norm(matriz_corr[fila, columna])))
            )

    ax.set_title("Mapa de calor de correlaciones")
    return fig


def grafica_barras_error(d: Datos, p: Paleta):
    """Mostrar una estimación y su incertidumbre."""
    promedios = np.array([72, 80, 77, 85, 90])
    errores = np.array([4, 3, 5, 2, 4])

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.errorbar(
        d.productos,
        promedios,
        yerr=errores,
        fmt="o",
        capsize=6,
        color=p.principal,
        ecolor=p.acento,
        markersize=7
    )

    ax.set_title("Promedio y margen simulado por producto")
    ax.set_ylabel("Valor promedio (unidades arbitrarias)")
    ax.grid(axis="y")
    return fig


def grafica_escalones(d: Datos, p: Paleta):
    """Valores que cambian por periodos o etapas."""
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.step(
        d.meses,
        d.ventas,
        where="mid",
        color=p.extra,
        linewidth=2.5,
        label="Ventas"
    )

    ax.set_title("Evolución escalonada de ventas")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Ventas (miles de pesos)")
    ax.legend()
    ax.grid(True)
    return fig


def grafica_tallos(d: Datos, p: Paleta):
    """Visualizar valores discretos y sus magnitudes."""
    fig, ax = plt.subplots(figsize=(9, 5))

    marcadores, tallos, base = ax.stem(
        np.arange(1, 13),
        d.ventas,
        linefmt="-",
        markerfmt="o",
        basefmt="-"
    )

    ax.set_title("Ventas por periodo: gráfico de tallos")
    ax.set_xlabel("Periodo")
    ax.set_ylabel("Ventas (miles de pesos)")
    ax.grid(axis="y")
    plt.setp(marcadores, color=p.principal)
    plt.setp(tallos, color=p.principal)
    plt.setp(base, color="#64748B")
    return fig


def grafica_hexbin(d: Datos, p: Paleta):
    """Visualizar concentraciones cuando hay muchos puntos y un scatter normal se vuelve difícil de leer."""
    rng_hex = np.random.default_rng(10)

    x_hex = rng_hex.normal(0, 1, 1500)
    y_hex = 0.6 * x_hex + rng_hex.normal(0, 0.8, 1500)

    fig, ax = plt.subplots(figsize=(8, 5))

    hexagonos = ax.hexbin(
        x_hex,
        y_hex,
        gridsize=30,
        cmap=p.secuencial,
        mincnt=1
    )

    fig.colorbar(hexagonos, ax=ax, label="Cantidad de puntos")

    ax.set_title("Concentración de observaciones")
    ax.set_xlabel("Variable X")
    ax.set_ylabel("Variable Y")
    return fig


def grafica_curvas_nivel(d: Datos, p: Paleta):
    """Representar una función con dos variables."""
    X, Y, Z = malla_funcion()

    fig, ax = plt.subplots(figsize=(8, 6))

    niveles = ax.contourf(
        X,
        Y,
        Z,
        levels=np.linspace(-1, 1, 21),
        vmin=-1, vmax=1,
        cmap=p.divergente
    )

    fig.colorbar(niveles, ax=ax, label="Valor de la función")

    ax.set_title("Curvas de nivel de una función")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    return fig


def grafica_superficie_3d(d: Datos, p: Paleta):
    """Estudiar funciones con dos variables independientes."""
    X, Y, Z = malla_funcion()

    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(111, projection="3d")

    superficie = ax.plot_surface(
        X,
        Y,
        Z,
        cmap=p.divergente,
        vmin=-1, vmax=1,
        edgecolor="none",
        alpha=0.9
    )

    fig.colorbar(superficie, ax=ax, shrink=0.6, label="Z")

    ax.set_title("Superficie tridimensional")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    return fig


def grafica_polar(d: Datos, p: Paleta):
    """Datos relacionados con ángulos, dirección o ciclos."""
    angulos = np.linspace(0, 2 * np.pi, 360)
    radio = 2 + np.sin(4 * angulos)

    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection="polar")

    ax.plot(
        angulos,
        radio,
        color=p.secundario,
        linewidth=2
    )

    ax.set_title("Visualización en coordenadas polares", pad=20)
    return fig


def grafica_funcion_relleno(d: Datos, p: Paleta):
    """Resaltar máximos, mínimos o regiones de interés."""
    x_funcion = np.linspace(0, 2 * np.pi, 500)

    y_funcion = (
        np.sin(x_funcion)
        + 0.5 * np.sin(3 * x_funcion)
        + 0.2 * np.sin(5 * x_funcion)
    )

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        x_funcion,
        y_funcion,
        color=p.principal,
        linewidth=2.5,
        label="f(x)"
    )

    ax.fill_between(
        x_funcion,
        y_funcion,
        0,
        where=(y_funcion >= 0),
        color=p.secundario,
        alpha=0.3,
        interpolate=True
    )

    ax.fill_between(
        x_funcion,
        y_funcion,
        0,
        where=(y_funcion < 0),
        color=p.acento,
        alpha=0.3,
        interpolate=True
    )

    ax.axhline(0, color="gray", linewidth=1)
    ax.set_title("Función matemática con regiones resaltadas")
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    ax.legend()
    ax.grid(True)
    return fig

# Número, nombre de archivo, título, propósito y función de dibujo.
CATALOGO = {
    1: ("01_lineas", 'Líneas', 'observar tendencias a través del tiempo.', grafica_lineas),
    2: ("02_lineas_multiples", 'Líneas múltiples', 'comparar varias series a través del tiempo.', grafica_lineas_multiples),
    3: ("03_barras_verticales", 'Barras verticales', 'comparar categorías.', grafica_barras_verticales),
    4: ("04_barras_horizontales", 'Barras horizontales', 'categorías con nombres largos.', grafica_barras_horizontales),
    5: ("05_barras_agrupadas", 'Barras agrupadas', 'comparar dos o más grupos por categoría.', grafica_barras_agrupadas),
    6: ("06_barras_apiladas", 'Barras apiladas', 'mostrar componentes de un total.', grafica_barras_apiladas),
    7: ("07_area", 'Área', 'destacar la magnitud mensual; no representa un acumulado.', grafica_area),
    8: ("08_areas_apiladas", 'Áreas apiladas', 'comparar la composición de varias series.', grafica_areas_apiladas),
    9: ("09_pastel", 'Pastel', 'mostrar proporciones de un total.', grafica_pastel),
    10: ("10_dona", 'Dona', 'proporciones con un espacio central para destacar un indicador o texto.', grafica_dona),
    11: ("11_histograma", 'Histograma', 'observar la distribución de una variable numérica.', grafica_histograma),
    12: ("12_caja_bigotes", 'Caja y bigotes', 'comparar medianas, dispersión y posibles valores atípicos entre grupos.', grafica_caja_bigotes),
    13: ("13_violin", 'Violín', 'observar la forma de la distribución de cada grupo.', grafica_violin),
    14: ("14_dispersion", 'Dispersión', 'investigar la relación entre dos variables.', grafica_dispersion),
    15: ("15_burbujas", 'Burbujas', 'representar tres variables numéricas. X e Y son posiciones; el tamaño representa una tercera variable.', grafica_burbujas),
    16: ("16_mapa_calor", 'Mapa de calor de correlación', 'observar relaciones lineales entre variables.', grafica_mapa_calor),
    17: ("17_barras_error", 'Barras de error', 'mostrar una estimación y su incertidumbre.', grafica_barras_error),
    18: ("18_escalones", 'Escalones', 'valores que cambian por periodos o etapas.', grafica_escalones),
    19: ("19_tallos", 'Stem o tallos', 'visualizar valores discretos y sus magnitudes.', grafica_tallos),
    20: ("20_hexbin", 'Hexbin', 'visualizar concentraciones cuando hay muchos puntos y un scatter normal se vuelve difícil de leer.', grafica_hexbin),
    21: ("21_curvas_nivel", 'Curvas de nivel', 'representar una función con dos variables.', grafica_curvas_nivel),
    22: ("22_superficie_3d", 'Superficie 3d', 'estudiar funciones con dos variables independientes.', grafica_superficie_3d),
    23: ("23_polar", 'Coordenadas polares', 'datos relacionados con ángulos, dirección o ciclos.', grafica_polar),
    24: ("24_funcion_relleno", 'Función matemática con relleno', 'resaltar máximos, mínimos o regiones de interés.', grafica_funcion_relleno),
}
