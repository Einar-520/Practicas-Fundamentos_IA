"""Búsqueda de costo uniforme: prioridad por g(n), sin heurística."""
from dataclasses import dataclass
import heapq
from itertools import count
import math


# Conexiones y costos de la imagen de clase, de padre a hijo.
GRAFO_ORIGINAL = {
    "A": {"B": 2, "C": 3},
    "B": {"D": 4, "E": 1},
    "C": {"F": 2, "G": 6},
    "D": {"H": 3},
    "E": {"I": 2},
    "F": {"J": 3},
    "G": {}, "H": {}, "I": {}, "J": {},
}


@dataclass(frozen=True)
class Alternativa:
    costo: float
    camino: tuple[str, ...]

    @property
    def estado(self):
        return self.camino[-1]


@dataclass(frozen=True)
class Paso:
    evento: str
    actual: str | None
    costo: float | None
    camino: tuple[str, ...]
    visitados: tuple[str, ...]
    frontera: tuple[Alternativa, ...]
    mensaje: str

    @property
    def profundidad(self):
        return len(self.camino) - 1 if self.camino else None


@dataclass(frozen=True)
class Resultado:
    ruta: tuple[str, ...] | None
    costo: float | None
    orden: tuple[str, ...]
    pasos: tuple[Paso, ...]


def validar_grafo(grafo):
    """Devuelve una copia con costos finitos y no negativos, necesarios para UCS."""
    if not isinstance(grafo, dict) or not grafo:
        raise ValueError("El grafo debe contener al menos un estado.")
    if any(not isinstance(nodo, str) or not nodo.strip() for nodo in grafo):
        raise ValueError("Cada estado debe tener un nombre de texto no vacío.")
    copia = {}
    for origen, vecinos in grafo.items():
        if not isinstance(vecinos, dict):
            raise ValueError(f"Los vecinos de {origen} deben indicar destino y costo.")
        copia[origen] = {}
        for destino, valor in vecinos.items():
            if destino not in grafo:
                raise ValueError(f"El destino {destino} no existe en el grafo.")
            try:
                if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                    raise ValueError
                costo = float(valor)
                if not math.isfinite(costo) or costo < 0:
                    raise ValueError
            except (ValueError, OverflowError):
                raise ValueError(f"El costo de {origen} a {destino} debe ser un número finito mayor o igual a cero.") from None
            copia[origen][destino] = costo
    return copia


def ucs(grafo, inicio="A", objetivo="J"):
    """Encuentra una ruta de costo mínimo en un grafo finito de pesos no negativos.

    Las entradas del heap son (costo acumulado, turno, estado, camino).
    El turno mantiene el orden de llegada cuando dos costos son iguales.
    """
    grafo = validar_grafo(grafo)
    if not isinstance(inicio, str) or not isinstance(objetivo, str) or inicio not in grafo or objetivo not in grafo:
        raise ValueError("El inicio y el objetivo deben existir en el grafo.")
    turnos = count()
    frontera = []
    heapq.heappush(frontera, (0.0, next(turnos), inicio, (inicio,)))
    mejores = {inicio: 0.0}
    resueltos, orden, pasos = set(), [], []

    def frontera_visible():
        # Se ordena una COPIA para mostrarla; las extracciones usan heapq.
        # Las entradas antiguas sustituidas por un costo mejor no se muestran.
        return tuple(Alternativa(costo, camino)
                     for costo, _, estado, camino in sorted(frontera)
                     if estado not in resueltos and costo == mejores[estado])

    while frontera:
        costo, _, actual, camino = heapq.heappop(frontera)
        if actual in resueltos or costo != mejores[actual]:
            continue
        resueltos.add(actual)
        orden.append(actual)
        # La meta se comprueba al EXTRAER el mínimo, no al descubrir un vecino.
        if actual == objetivo:
            pasos.append(Paso("Meta", actual, costo, camino, tuple(orden), frontera_visible(),
                              f"Se extrae {actual} con g(n) = {costo:g}. Es la meta: costo mínimo confirmado."))
            return Resultado(camino, costo, tuple(orden), tuple(pasos))

        cambios = []
        for vecino, peso in grafo[actual].items():
            if vecino in resueltos:
                continue
            nuevo_costo = costo + peso
            if not math.isfinite(nuevo_costo):
                raise ValueError("El costo acumulado es demasiado grande. Usa valores menores.")
            if nuevo_costo < mejores.get(vecino, math.inf):
                mejores[vecino] = nuevo_costo
                heapq.heappush(frontera, (nuevo_costo, next(turnos), vecino, camino + (vecino,)))
                cambios.append(f"{vecino}: {costo:g} + {peso:g} = {nuevo_costo:g}")
        detalle = "; ".join(cambios) if cambios else "No hay vecinos nuevos con un costo mejor."
        pasos.append(Paso("Explorar", actual, costo, camino, tuple(orden), frontera_visible(),
                          f"Se extrae {actual}, mínimo pendiente con g(n) = {costo:g}. {detalle}"))

    pasos.append(Paso("Sin ruta", None, None, (), tuple(orden), (),
                      f"La cola quedó vacía. No existe una ruta de {inicio} a {objetivo}."))
    return Resultado(None, None, tuple(orden), tuple(pasos))
