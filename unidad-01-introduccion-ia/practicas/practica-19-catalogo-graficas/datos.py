"""Datos ficticios del ejercicio; las semillas permiten comparar las paletas."""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Datos:
    meses: tuple[str, ...]
    ventas: np.ndarray
    costos: np.ndarray
    utilidad: np.ndarray
    productos: tuple[str, ...]
    ventas_productos: np.ndarray
    categorias: tuple[str, ...]
    participacion: tuple[int, ...]
    calificaciones: np.ndarray
    horas_estudio: np.ndarray
    notas: np.ndarray
    grupo_a: np.ndarray
    grupo_b: np.ndarray
    grupo_c: np.ndarray
    variable_adicional: np.ndarray


def generar_datos() -> Datos:
    """Cambiar aquí los datos compartidos; no se consultan servicios externos."""
    ventas = np.array([85, 92, 88, 105, 110, 120, 115, 130, 125, 140, 155, 170])
    costos = np.array([50, 55, 52, 61, 65, 70, 68, 75, 72, 80, 88, 95])
    rng = np.random.default_rng(42)
    calificaciones = np.clip(rng.normal(82, 10, 200), 0, 100)
    horas = rng.uniform(1, 10, 100)
    notas = np.clip(45 + 5 * horas + rng.normal(0, 8, 100), 0, 100)
    grupo_a = rng.normal(75, 8, 80)
    grupo_b = rng.normal(82, 6, 80)
    grupo_c = rng.normal(78, 10, 80)
    return Datos(
        meses=("Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"),
        ventas=ventas, costos=costos, utilidad=ventas-costos,
        productos=("Laptop", "Monitor", "Teclado", "Mouse", "Audífonos"),
        ventas_productos=np.array([120, 95, 180, 210, 145]),
        categorias=("Electrónica", "Accesorios", "Mobiliario", "Otros"),
        participacion=(40, 30, 20, 10),
        calificaciones=calificaciones, horas_estudio=horas, notas=notas,
        grupo_a=grupo_a, grupo_b=grupo_b, grupo_c=grupo_c,
        variable_adicional=rng.normal(75, 8, len(notas)),
    )
