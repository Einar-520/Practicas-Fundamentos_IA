"""Asignación uno a uno de cuatro empleados a cuatro turnos."""
from dataclasses import dataclass
from itertools import combinations, permutations


EMPLEADOS = ("Ana", "Luis", "Carlos", "María")
TURNOS = ("Mañana", "Tarde", "Noche", "Mixto")
PREFERENCIAS = ("Mañana", "Tarde", "Noche", "Mañana")
# Inicio didáctico para observar dos mejoras. Cada turno aparece una sola vez.
INICIO = ("Tarde", "Noche", "Mixto", "Mañana")


@dataclass(frozen=True)
class Paso:
    asignacion: tuple[str, ...]
    satisfaccion: int
    intercambio: tuple[str, str] | None = None


@dataclass(frozen=True)
class Resultado:
    pasos: tuple[Paso, ...]
    vecinos_evaluados: int

    @property
    def final(self):
        return self.pasos[-1]


@dataclass(frozen=True)
class Verificacion:
    satisfaccion: int
    asignaciones: tuple[tuple[str, ...], ...]
    examinadas: int


def validar_asignacion(asignacion):
    asignacion = tuple(asignacion)
    if len(asignacion) != len(EMPLEADOS):
        raise ValueError("Asigna exactamente un turno a cada uno de los cuatro empleados.")
    if any(not isinstance(turno, str) or turno not in TURNOS for turno in asignacion):
        raise ValueError("Los turnos permitidos son Mañana, Tarde, Noche y Mixto.")
    if len(set(asignacion)) != len(TURNOS):
        raise ValueError("No se pueden repetir turnos: cada turno corresponde a un empleado.")
    return asignacion


def validar_preferencias(preferencias):
    preferencias = tuple(preferencias)
    if len(preferencias) != len(EMPLEADOS) or any(p not in TURNOS for p in preferencias):
        raise ValueError("Indica una preferencia válida por cada empleado.")
    return preferencias


def puntuar(asignacion, preferencias=PREFERENCIAS):
    """Un punto por coincidencia; cero por un turno diferente, incluido Mixto."""
    return sum(turno == preferido for turno, preferido in zip(asignacion, preferencias))


def vecinos(asignacion):
    """Los seis vecinos intercambian los turnos de una pareja de empleados."""
    for i, j in combinations(range(len(EMPLEADOS)), 2):
        nueva = list(asignacion)
        nueva[i], nueva[j] = nueva[j], nueva[i]
        yield (EMPLEADOS[i], EMPLEADOS[j]), tuple(nueva)


def hill_climbing(inicio=INICIO, preferencias=PREFERENCIAS):
    """Elige el mejor intercambio; se detiene cuando ninguno mejora estrictamente.

    En empate entre vecinos mejores, conserva el primero en el orden de
    EMPLEADOS. No hay movimientos laterales, retrocesos ni búsqueda exhaustiva.
    """
    actual = validar_asignacion(inicio)
    preferencias = validar_preferencias(preferencias)
    paso = Paso(actual, puntuar(actual, preferencias))
    pasos, evaluados = [paso], 0
    while True:
        mejor = paso
        for intercambio, candidato in vecinos(paso.asignacion):
            evaluados += 1
            puntuacion = puntuar(candidato, preferencias)
            if puntuacion > mejor.satisfaccion:
                mejor = Paso(candidato, puntuacion, intercambio)
        if mejor is paso:
            return Resultado(tuple(pasos), evaluados)
        paso = mejor
        pasos.append(paso)


def verificar_optimas(preferencias=PREFERENCIAS):
    """Comprobación independiente de las 4! = 24 asignaciones posibles."""
    preferencias = validar_preferencias(preferencias)
    mayor, mejores, examinadas = -1, [], 0
    for asignacion in permutations(TURNOS):
        examinadas += 1
        puntos = puntuar(asignacion, preferencias)
        if puntos > mayor:
            mayor, mejores = puntos, [asignacion]
        elif puntos == mayor:
            mejores.append(asignacion)
    return Verificacion(mayor, tuple(mejores), examinadas)


def descripcion(asignacion):
    return " | ".join(f"{empleado}: {turno}" for empleado, turno in zip(EMPLEADOS, asignacion))
