"""Comprueba las reglas y los 24 puntos de partida posibles del ejercicio."""
from itertools import permutations
import unittest

from asignacion import (
    EMPLEADOS, TURNOS, INICIO, PREFERENCIAS, hill_climbing,
    puntuar, validar_asignacion, vecinos, verificar_optimas,
)


class PruebasAsignacion(unittest.TestCase):
    def test_dos_optimas_y_limite_de_satisfaccion(self):
        exacta = verificar_optimas()
        self.assertEqual(exacta.examinadas, 24)
        self.assertEqual(exacta.satisfaccion, 3)
        self.assertEqual(set(exacta.asignaciones), {
            ('Mañana', 'Tarde', 'Noche', 'Mixto'),
            ('Mixto', 'Tarde', 'Noche', 'Mañana'),
        })
        self.assertEqual(exacta.satisfaccion / len(EMPLEADOS), .75)

    def test_recorrido_didactico(self):
        resultado = hill_climbing()
        self.assertEqual([paso.satisfaccion for paso in resultado.pasos], [1, 2, 3])
        self.assertEqual(resultado.pasos[0].asignacion, INICIO)
        self.assertEqual(resultado.final.asignacion, ('Mixto', 'Tarde', 'Noche', 'Mañana'))
        self.assertEqual(resultado.pasos[1].intercambio, ('Ana', 'Luis'))
        self.assertEqual(resultado.pasos[2].intercambio, ('Ana', 'Carlos'))

    def test_todas_las_asignaciones_iniciales(self):
        optimas = set(verificar_optimas().asignaciones)
        for inicio in permutations(TURNOS):
            with self.subTest(inicio=inicio):
                resultado = hill_climbing(inicio)
                self.assertIn(resultado.final.asignacion, optimas)
                for paso in resultado.pasos:
                    self.assertEqual(set(paso.asignacion), set(TURNOS))
                    esperado = sum(1 for i in range(4) if paso.asignacion[i] == PREFERENCIAS[i])
                    self.assertEqual(paso.satisfaccion, esperado)
                for anterior, siguiente in zip(resultado.pasos, resultado.pasos[1:]):
                    self.assertGreater(siguiente.satisfaccion, anterior.satisfaccion)
                    cambiados = [i for i in range(4) if anterior.asignacion[i] != siguiente.asignacion[i]]
                    self.assertEqual(len(cambiados), 2)
                    i, j = cambiados
                    self.assertEqual(anterior.asignacion[i], siguiente.asignacion[j])
                    self.assertEqual(anterior.asignacion[j], siguiente.asignacion[i])
                for _, vecino in vecinos(resultado.final.asignacion):
                    self.assertLessEqual(puntuar(vecino), resultado.final.satisfaccion)

    def test_inicio_optimo_no_hace_movimientos(self):
        for inicio in verificar_optimas().asignaciones:
            self.assertEqual(len(hill_climbing(inicio).pasos), 1)

    def test_seis_vecinos_distintos_y_factibles(self):
        estados = [estado for _, estado in vecinos(INICIO)]
        self.assertEqual(len(set(estados)), 6)
        for estado in estados:
            self.assertNotEqual(estado, INICIO)
            self.assertEqual(validar_asignacion(estado), estado)

    def test_rechaza_asignaciones_invalidas(self):
        for estado in ((), TURNOS[:3], (*TURNOS, 'Mañana'), ('Mañana',) * 4,
                       ('Mañana', 'Tarde', 'Noche', 'Desconocido'), (1, 2, 3, 4)):
            with self.subTest(estado=estado), self.assertRaises(ValueError):
                hill_climbing(estado)
        with self.assertRaises(ValueError):
            hill_climbing(preferencias=('Mañana',))


if __name__ == '__main__':
    unittest.main()
