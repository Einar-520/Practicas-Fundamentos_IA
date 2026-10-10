"""A*: costo recorrido g(n) + estimación h(n), con prioridad en un heap."""
from dataclasses import dataclass
import heapq
from itertools import count
import math


# Imagen de esta práctica: aristas dirigidas de padre a hijo.
# No se indicaron pesos: cada movimiento cuesta 1, editable en la interfaz.
GRAFO_ORIGINAL = {
    "A": {"B": 1, "C": 1},
    "B": {"D": 1, "E": 1},
    "C": {"F": 1, "G": 1},
    "D": {"H": 1}, "E": {}, "F": {"I": 1},
    "G": {}, "H": {}, "I": {"J": 1}, "J": {},
}
HEURISTICA_ORIGINAL = {
    "A": 7, "B": 6, "C": 4, "D": 7, "E": 5,
    "F": 3, "G": 6, "H": 8, "I": 1, "J": 0,
}


@dataclass(frozen=True)
class Alternativa:
    g: float
    h: float
    camino: tuple[str, ...]

    @property
    def estado(self):
        return self.camino[-1]

    @property
    def f(self):
        return self.g + self.h


@dataclass(frozen=True)
class Paso:
    evento: str
    actual: str | None
    g: float | None
    h: float | None
    camino: tuple[str, ...]
    visitados: tuple[str, ...]
    frontera: tuple[Alternativa, ...]
    mensaje: str

    @property
    def f(self):
        return None if self.g is None else self.g + self.h

    @property
    def profundidad(self):
        return len(self.camino) - 1 if self.camino else None


@dataclass(frozen=True)
class Resultado:
    ruta: tuple[str, ...] | None
    costo: float | None
    orden: tuple[str, ...]
    pasos: tuple[Paso, ...]


def numero_no_negativo(valor, etiqueta):
    """Rechaza texto, booleanos, negativos, NaN, infinitos y desbordamientos."""
    try:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValueError
        numero = float(valor)
        if not math.isfinite(numero) or numero < 0:
            raise ValueError
    except (ValueError, OverflowError):
        raise ValueError(f"{etiqueta} debe ser un número finito mayor o igual a cero.") from None
    return numero


def sumar(a, b):
    resultado = a + b
    if not math.isfinite(resultado):
        raise ValueError("El costo o la estimación total es demasiado grande. Usa valores menores.")
    return resultado


def validar_problema(grafo, heuristica, inicio="A", objetivo="J"):
    """Devuelve copias validadas sin modificar los datos recibidos."""
    if not isinstance(grafo, dict) or not grafo:
        raise ValueError("El grafo debe ser un diccionario con al menos un estado.")
    if any(not isinstance(nodo, str) or not nodo.strip() for nodo in grafo):
        raise ValueError("Los estados deben tener nombres de texto no vacíos.")
    if (not isinstance(inicio, str) or not isinstance(objetivo, str)
            or inicio not in grafo or objetivo not in grafo):
        raise ValueError("El inicio y el objetivo deben existir en el grafo.")
    copia = {}
    for origen, vecinos in grafo.items():
        if not isinstance(vecinos, dict):
            raise ValueError(f"Los vecinos de {origen} deben indicar destino y costo.")
        copia[origen] = {}
        for destino, costo in vecinos.items():
            if destino not in grafo:
                raise ValueError(f"El destino {destino} no existe en el grafo.")
            copia[origen][destino] = numero_no_negativo(costo, f"El costo de {origen} a {destino}")
    if not isinstance(heuristica, dict) or set(heuristica) != set(grafo):
        raise ValueError("Debe existir una estimación h(n) para cada estado y solo para esos estados.")
    h = {nodo: numero_no_negativo(valor, f"h({nodo})") for nodo, valor in heuristica.items()}
    if h[objetivo] != 0:
        raise ValueError(f"h({objetivo}) debe ser 0: al llegar a la meta no falta recorrido.")
    return copia, h


def a_estrella(grafo, heuristica, inicio="A", objetivo="J"):
    """Extrae el menor f(n) y reabre estados si descubre un g(n) menor.

    Con h admisible y h(meta)=0 devuelve costo mínimo. Una h que sobreestima
    puede producir una solución subóptima en grafos con rutas alternativas.
    Los empates de f se resuelven por orden de inserción.
    """
    grafo, h = validar_problema(grafo, heuristica, inicio, objetivo)
    turnos = count()
    frontera = [(h[inicio], next(turnos), 0.0, inicio, (inicio,))]
    mejores = {inicio: 0.0}
    expandidos, orden, pasos = {}, [], []

    def vigente(g, nodo):
        return g == mejores[nodo] and (nodo not in expandidos or g < expandidos[nodo])

    def frontera_visible():
        # Solo se ordena una copia para la tabla; el algoritmo extrae del heap.
        return tuple(Alternativa(g, h[nodo], camino)
                     for _, _, g, nodo, camino in sorted(frontera) if vigente(g, nodo))

    while frontera:
        f, _, g, actual, camino = heapq.heappop(frontera)
        if not vigente(g, actual):
            continue  # Entrada antigua: ya existe una ruta mejor.
        reabierto = actual in expandidos
        expandidos[actual] = g
        orden.append(actual)
        detalle = f"Se extrae {actual}: f(n) = g(n) + h(n) = {g:g} + {h[actual]:g} = {f:g}."
        # La meta se comprueba al extraer, nunca al insertarla en el heap.
        if actual == objetivo:
            pasos.append(Paso("Meta", actual, g, h[actual], camino, tuple(orden),
                              frontera_visible(), detalle + " Se alcanzó la meta."))
            return Resultado(camino, g, tuple(orden), tuple(pasos))
        cambios = []
        for vecino, peso in grafo[actual].items():
            nuevo_g = sumar(g, peso)
            if nuevo_g < mejores.get(vecino, math.inf):
                nuevo_f = sumar(nuevo_g, h[vecino])
                mejores[vecino] = nuevo_g
                heapq.heappush(frontera, (nuevo_f, next(turnos), nuevo_g, vecino, camino + (vecino,)))
                cambios.append(f"{vecino}: g={g:g}+{peso:g}={nuevo_g:g}, h={h[vecino]:g}, f={nuevo_f:g}")
        detalle += " " + ("; ".join(cambios) if cambios else "No hay vecinos con una mejora de g(n).")
        pasos.append(Paso("Reexplorar" if reabierto else "Explorar", actual, g, h[actual],
                          camino, tuple(orden), frontera_visible(), detalle))
    pasos.append(Paso("Sin ruta", None, None, None, (), tuple(orden), (),
                      f"La frontera quedó vacía. No hay ruta de {inicio} a {objetivo}."))
    return Resultado(None, None, tuple(orden), tuple(pasos))


@dataclass(frozen=True)
class DiagnosticoHeuristica:
    distancias: dict[str, float]
    sobreestimados: tuple[str, ...]
    inconsistencias: tuple[tuple[str, str], ...]

    @property
    def admisible(self):
        return not self.sobreestimados


def analizar_heuristica(grafo, heuristica, objetivo="J"):
    """Comprueba h contra costos reales en este grafo pequeño, solo para explicar.

    Esta revisión usa Dijkstra desde la meta sobre las aristas invertidas.
    A* no recibe ni utiliza estas distancias para elegir su siguiente estado.
    """
    grafo, h = validar_problema(grafo, heuristica, objetivo, objetivo)
    inverso = {nodo: {} for nodo in grafo}
    for origen, vecinos in grafo.items():
        for destino, costo in vecinos.items():
            inverso[destino][origen] = costo
    distancias = {nodo: math.inf for nodo in grafo}
    distancias[objetivo] = 0.0
    pendientes = [(0.0, objetivo)]
    while pendientes:
        costo, actual = heapq.heappop(pendientes)
        if costo != distancias[actual]:
            continue
        for vecino, peso in inverso[actual].items():
            candidato = sumar(costo, peso)
            if candidato < distancias[vecino]:
                distancias[vecino] = candidato
                heapq.heappush(pendientes, (candidato, vecino))
    sobreestimados = tuple(nodo for nodo in grafo if h[nodo] > distancias[nodo])
    inconsistencias = tuple((o, d) for o, vecinos in grafo.items() for d, costo in vecinos.items()
                            if h[o] > costo + h[d])
    return DiagnosticoHeuristica(distancias, sobreestimados, inconsistencias)
