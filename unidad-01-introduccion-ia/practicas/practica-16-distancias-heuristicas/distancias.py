"""Distancias geométricas entre dos puntos del plano; sin dependencias gráficas."""
from dataclasses import dataclass
import math


PUNTO_A = (1.0, 2.0)
PUNTO_B = (5.0, 5.0)


@dataclass(frozen=True)
class Medicion:
    a: tuple[float, float]
    b: tuple[float, float]
    dx: float
    dy: float
    manhattan: float
    euclidiana: float

    @property
    def diferencia(self):
        return self.manhattan - self.euclidiana


def validar_punto(punto, nombre):
    if not isinstance(punto, (tuple, list)) or len(punto) != 2:
        raise ValueError(f"El punto {nombre} debe contener dos coordenadas: X e Y.")
    valores = []
    for eje, valor in zip(("X", "Y"), punto):
        try:
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise ValueError
            numero = float(valor)
            if not math.isfinite(numero):
                raise ValueError
        except (ValueError, OverflowError):
            raise ValueError(f"{nombre}.{eje} debe ser un número finito.") from None
        valores.append(numero)
    return tuple(valores)


def calcular_distancias(a=PUNTO_A, b=PUNTO_B):
    """L1 = |Δx| + |Δy|; L2 = sqrt(Δx² + Δy²), calculada con hypot."""
    a, b = validar_punto(a, "A"), validar_punto(b, "B")
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    manhattan = dx + dy
    euclidiana = math.hypot(dx, dy)
    if not math.isfinite(manhattan) or not math.isfinite(euclidiana):
        raise ValueError("Las coordenadas producen una distancia demasiado grande. Usa valores menores.")
    return Medicion(a, b, dx, dy, manhattan, euclidiana)


def ruta_manhattan(medicion, orden="xy"):
    """Una ruta mínima por ejes; no es la única ruta Manhattan posible."""
    if orden not in ("xy", "yx"):
        raise ValueError("El orden debe ser 'xy' o 'yx'.")
    a, b = medicion.a, medicion.b
    esquina = (b[0], a[1]) if orden == "xy" else (a[0], b[1])
    return a, esquina, b


def numero(valor):
    """Formato legible; el cálculo conserva la precisión del float."""
    return f"{valor:.6g}"


def texto_punto(punto):
    return f"({numero(punto[0])}, {numero(punto[1])})"


def conclusion(medicion):
    if medicion.manhattan == 0:
        return "A y B coinciden: ambas distancias son 0."
    if medicion.dx == 0 or medicion.dy == 0:
        return "Los puntos comparten un eje: los dos recorridos coinciden."
    return f"El recorrido por ejes mide {numero(medicion.diferencia)} unidades más que la línea recta."
