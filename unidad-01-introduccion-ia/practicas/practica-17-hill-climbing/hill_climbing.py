"""Búsqueda local por mejor mejora; los cálculos no dependen de la interfaz."""
from dataclasses import dataclass
from itertools import combinations
from math import isfinite


LISTA = (2, 5, 8, 12, 9, 6, 3)
PRESUPUESTO = 1000


@dataclass(frozen=True)
class Producto:
    nombre: str
    costo: int
    beneficio: int


PRODUCTOS = (
    Producto("A", 200, 30), Producto("B", 300, 50),
    Producto("C", 400, 70), Producto("D", 250, 40), Producto("E", 350, 60),
)


@dataclass(frozen=True)
class ResultadoLista:
    valores: tuple[float, ...]
    indices: tuple[int, ...]

    @property
    def valor_final(self):
        return self.valores[self.indices[-1]]

    @property
    def recorrido(self):
        return tuple(self.valores[i] for i in self.indices)


@dataclass(frozen=True)
class Seleccion:
    productos: tuple[str, ...]
    costo: int
    beneficio: int


@dataclass(frozen=True)
class ResultadoProductos:
    pasos: tuple[Seleccion, ...]
    vecinos_evaluados: int

    @property
    def final(self):
        return self.pasos[-1]


@dataclass(frozen=True)
class VerificacionExacta:
    soluciones: tuple[Seleccion, ...]
    combinaciones: int
    factibles: int

    @property
    def beneficio(self):
        return self.soluciones[0].beneficio


def numero(valor):
    return f"{valor:g}"


def nombres(seleccion):
    return ", ".join(seleccion.productos) or "Ninguno"


def subir_lista(valores=LISTA, inicio=0):
    """Compara ambos vecinos adyacentes; solo acepta mejoras estrictas.

    El índice inicial usa base cero. En un empate entre vecinos mejores,
    se elige el de menor índice. La traza sirve para explicar y graficar.
    """
    valores = tuple(valores)
    if not valores or any(isinstance(v, bool) or not isinstance(v, (int, float))
                          or not isfinite(v) for v in valores):
        raise ValueError("La lista debe contener números finitos y no estar vacía.")
    if type(inicio) is not int or not 0 <= inicio < len(valores):
        raise ValueError("La posición inicial debe existir en la lista.")
    actual, indices = inicio, [inicio]
    while True:
        mejor = actual
        for vecino in (actual - 1, actual + 1):
            if 0 <= vecino < len(valores) and valores[vecino] > valores[mejor]:
                mejor = vecino
        if mejor == actual:
            return ResultadoLista(valores, tuple(indices))
        actual = mejor
        indices.append(actual)


def validar_productos(productos, presupuesto):
    if type(presupuesto) is not int or presupuesto < 0:
        raise ValueError("El presupuesto debe ser un número entero de pesos, mayor o igual a cero.")
    if not productos:
        raise ValueError("Debe existir al menos un producto.")
    catalogo = {}
    for producto in productos:
        if not isinstance(producto, Producto) or not isinstance(producto.nombre, str) or not producto.nombre.strip():
            raise ValueError("Cada producto necesita un nombre de texto no vacío.")
        if producto.nombre in catalogo:
            raise ValueError("Los nombres de los productos no pueden repetirse.")
        if type(producto.costo) is not int or producto.costo <= 0:
            raise ValueError("Los costos deben ser enteros positivos de pesos.")
        if type(producto.beneficio) is not int or producto.beneficio < 0:
            raise ValueError("Los beneficios deben ser enteros no negativos.")
        catalogo[producto.nombre] = producto
    return catalogo


def evaluar(catalogo, elegidos):
    return Seleccion(tuple(sorted(elegidos)),
                     sum(catalogo[n].costo for n in elegidos),
                     sum(catalogo[n].beneficio for n in elegidos))


def vecinos_productos(elegidos, catalogo):
    """Genera vecinos uno a uno: agregar, retirar o intercambiar una unidad."""
    disponibles = sorted(set(catalogo) - elegidos)
    for nuevo in disponibles:
        yield elegidos | {nuevo}
    for anterior in sorted(elegidos):
        yield elegidos - {anterior}
        for nuevo in disponibles:
            yield (elegidos - {anterior}) | {nuevo}


def subir_productos(productos=PRODUCTOS, presupuesto=PRESUPUESTO, inicio=()):
    """Maximiza beneficio dentro del presupuesto; no garantiza el óptimo global.

    Desempata vecinos por menor costo y luego por nombres. Un empate de
    beneficio con el estado actual nunca causa movimiento (sin pasos laterales).
    """
    catalogo = validar_productos(productos, presupuesto)
    inicio = tuple(inicio)
    if any(not isinstance(n, str) or n not in catalogo for n in inicio):
        raise ValueError("La selección inicial contiene un producto desconocido.")
    if len(set(inicio)) != len(inicio):
        raise ValueError("Solo se permite una unidad de cada producto.")
    actual = evaluar(catalogo, frozenset(inicio))
    if actual.costo > presupuesto:
        raise ValueError("La selección inicial supera el presupuesto. Desmarca productos o aumenta el presupuesto.")
    pasos, evaluados = [actual], 0
    while True:
        mejor = actual
        for elegidos in vecinos_productos(frozenset(actual.productos), catalogo):
            candidato = evaluar(catalogo, elegidos)
            evaluados += 1
            if candidato.costo > presupuesto or candidato.beneficio <= actual.beneficio:
                continue
            clave = (-candidato.beneficio, candidato.costo, candidato.productos)
            if clave < (-mejor.beneficio, mejor.costo, mejor.productos):
                mejor = candidato
        if mejor == actual:
            return ResultadoProductos(tuple(pasos), evaluados)
        actual = mejor
        pasos.append(actual)


def verificar_optimo(productos=PRODUCTOS, presupuesto=PRESUPUESTO):
    """Comprobación exhaustiva independiente de Hill Climbing: 2**n subconjuntos.

    Solo se usa con catálogos pequeños. Devuelve todas las selecciones que
    empatan en el beneficio máximo, ordenadas por costo y nombres.
    """
    catalogo = validar_productos(productos, presupuesto)
    if len(catalogo) > 20:
        raise ValueError("La comprobación exhaustiva admite como máximo 20 productos.")
    soluciones, mayor, factibles = [], -1, 0
    for cantidad in range(len(catalogo) + 1):
        for grupo in combinations(sorted(catalogo), cantidad):
            candidato = evaluar(catalogo, grupo)
            if candidato.costo > presupuesto:
                continue
            factibles += 1
            if candidato.beneficio > mayor:
                mayor, soluciones = candidato.beneficio, [candidato]
            elif candidato.beneficio == mayor:
                soluciones.append(candidato)
    soluciones.sort(key=lambda s: (s.costo, s.productos))
    return VerificacionExacta(tuple(soluciones), 2 ** len(catalogo), factibles)


def leer_lista(texto):
    """Entrada de la interfaz: comas separadoras y punto para decimales."""
    try:
        valores = tuple(float(parte.strip()) for parte in texto.split(","))
    except ValueError:
        raise ValueError("Separa los números con comas y usa punto decimal: 2, 5, 8.5.") from None
    if not 1 <= len(valores) <= 40 or any(not isfinite(v) or abs(v) > 1_000_000 for v in valores):
        raise ValueError("El visor admite de 1 a 40 números finitos entre -1000000 y 1000000.")
    return valores
