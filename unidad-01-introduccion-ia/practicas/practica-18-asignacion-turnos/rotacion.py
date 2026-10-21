"""Calendario de turnos; conserva un empleado por turno en cada periodo."""
import csv
from dataclasses import dataclass
from pathlib import Path

from asignacion import EMPLEADOS, PREFERENCIAS, TURNOS, puntuar, validar_asignacion, verificar_optimas


MODOS = {
    "completa": "Todos pasan por los cuatro turnos",
    "preferencias": "Alternar Ana y María (75 %)",
}


@dataclass(frozen=True)
class Periodo:
    numero: int
    asignacion: tuple[str, ...]
    satisfaccion: int


@dataclass(frozen=True)
class Calendario:
    modo: str
    periodos: tuple[Periodo, ...]

    @property
    def porcentaje(self):
        return 100 * sum(p.satisfaccion for p in self.periodos) / (4 * len(self.periodos))

    @property
    def cumplimientos(self):
        return tuple(sum(p.asignacion[i] == preferencia for p in self.periodos)
                     for i, preferencia in enumerate(PREFERENCIAS))


def generar_rotacion(base, cantidad=4, modo="completa") -> Calendario:
    base = validar_asignacion(base)
    if type(cantidad) is not int or not 1 <= cantidad <= 52:
        raise ValueError("La cantidad de periodos debe ser un entero entre 1 y 52.")
    if modo not in MODOS:
        raise ValueError("Elige rotación completa o alternancia por preferencias.")
    if modo == "preferencias" and base not in verificar_optimas().asignaciones:
        raise ValueError("La alternancia por preferencias debe partir de una asignación óptima.")
    periodos = []
    for indice in range(cantidad):
        if modo == "completa":
            asignacion = tuple(TURNOS[(TURNOS.index(turno) + indice) % 4] for turno in base)
        else:
            asignacion = base if indice % 2 == 0 else (base[3], base[1], base[2], base[0])
        periodos.append(Periodo(indice + 1, asignacion, puntuar(asignacion)))
    return Calendario(modo, tuple(periodos))


def guardar_csv(calendario, destino):
    destino = Path(destino).expanduser().resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(("Periodo", *EMPLEADOS, "Preferencias cumplidas (de 4)", "Satisfacción", "Tipo de rotación"))
        for periodo in calendario.periodos:
            escritor.writerow((periodo.numero, *periodo.asignacion, periodo.satisfaccion,
                               f"{periodo.satisfaccion / 4:.0%}", MODOS[calendario.modo]))
    return destino
