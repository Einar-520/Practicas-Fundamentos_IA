"""Búsquedas sin heurística sobre los dos grafos originales del profesor."""
from collections import deque
from dataclasses import dataclass


GRAFO_BFS = {
    "A": ["B", "D"], "B": ["A", "C"], "C": ["B", "F"],
    "D": ["A", "E"], "E": ["D", "F"], "F": ["C", "E"],
}
GRAFO_DFS = {
    "A": ["B", "C"], "B": ["D", "E"], "C": ["F"],
    "D": [], "E": [], "F": [],
}


@dataclass(frozen=True)
class Paso:
    evento: str
    actual: str | None
    camino: tuple[str, ...]
    visitados: tuple[str, ...]
    pendientes: tuple[str, ...]
    mensaje: str


@dataclass(frozen=True)
class Resultado:
    ruta: tuple[str, ...] | None
    orden: tuple[str, ...]
    pasos: tuple[Paso, ...]

    @property
    def costo(self):
        """Cada arista cuesta una unidad; visitar el inicio no es un movimiento."""
        return None if self.ruta is None else len(self.ruta) - 1


def validar_problema(grafo, inicio, objetivo):
    if not isinstance(grafo, dict) or not grafo:
        raise ValueError("El grafo debe ser un diccionario con al menos un estado.")
    if any(not isinstance(nodo, str) or not nodo.strip() for nodo in grafo):
        raise ValueError("Los estados deben tener nombres de texto no vacíos.")
    for nodo, vecinos in grafo.items():
        if not isinstance(vecinos, (list, tuple)):
            raise ValueError(f"Los vecinos de {nodo} deben ser una lista ordenada.")
        if any(not isinstance(vecino, str) or vecino not in grafo for vecino in vecinos):
            raise ValueError(f"Hay un vecino de {nodo} que no existe en el grafo.")
    if inicio not in grafo or objetivo not in grafo:
        raise ValueError("El inicio y el objetivo deben existir en el grafo.")


def bfs(grafo, inicio="A", objetivo="F"):
    """Busca por niveles y devuelve la primera ruta de menor número de aristas."""
    validar_problema(grafo, inicio, objetivo)
    cola = deque([(inicio,)])
    descubiertos = {inicio}  # Se marca al encolar para evitar rutas duplicadas.
    orden, pasos = [], []
    while cola:
        camino = cola.popleft()
        actual = camino[-1]
        orden.append(actual)
        if actual == objetivo:
            pasos.append(Paso("Meta", actual, camino, tuple(orden),
                              tuple(ruta[-1] for ruta in cola),
                              f"Se alcanzó {objetivo}: ruta de costo {len(camino) - 1}."))
            return Resultado(camino, tuple(orden), tuple(pasos))
        for vecino in grafo[actual]:
            if vecino not in descubiertos:
                descubiertos.add(vecino)
                cola.append(camino + (vecino,))
        pasos.append(Paso("Explorar", actual, camino, tuple(orden),
                          tuple(ruta[-1] for ruta in cola),
                          f"Se explora {actual} y se encolan sus vecinos nuevos."))
    pasos.append(Paso("Sin ruta", None, (), tuple(orden), (),
                      f"Se agotó la cola. No hay ruta de {inicio} a {objetivo}."))
    return Resultado(None, tuple(orden), tuple(pasos))


def dfs(grafo, inicio="A", objetivo="F"):
    """Busca recursivamente; retrocede cuando una rama no conduce a la meta."""
    validar_problema(grafo, inicio, objetivo)
    visitados, orden, camino, pasos = set(), [], [], []

    def visitar(actual):
        visitados.add(actual)
        orden.append(actual)
        camino.append(actual)
        encontrado = actual == objetivo
        pasos.append(Paso("Meta" if encontrado else "Explorar", actual,
                          tuple(camino), tuple(orden), tuple(camino),
                          f"Se alcanzó {objetivo}." if encontrado else f"Se visita {actual}."))
        if encontrado:
            return tuple(camino)  # Copia inmutable, independiente del retroceso.
        for vecino in grafo[actual]:
            if vecino not in visitados:
                ruta = visitar(vecino)
                if ruta is not None:
                    return ruta
        camino.pop()
        pasos.append(Paso("Retroceso", camino[-1] if camino else None,
                          tuple(camino), tuple(orden), tuple(camino),
                          f"Se abandona la rama de {actual}: no lleva a la meta."))
        return None

    ruta = visitar(inicio)
    if ruta is None:
        pasos.append(Paso("Sin ruta", None, (), tuple(orden), (),
                          f"Se agotaron las ramas. No hay ruta de {inicio} a {objetivo}."))
    return Resultado(ruta, tuple(orden), tuple(pasos))
