"""Verifica propiedades de las distancias y su representación comparativa."""
import math
import unittest

from distancias import calcular_distancias, conclusion, ruta_manhattan
from grafica_distancias import crear_figura, validar_rango_grafico


class PruebasDistancias(unittest.TestCase):
    def test_ejercicio_3_4_5(self):
        m = calcular_distancias((1, 2), (5, 5))
        self.assertEqual((m.dx, m.dy, m.manhattan, m.euclidiana, m.diferencia), (4, 3, 7, 5, 2))
        self.assertEqual(ruta_manhattan(m), ((1, 2), (5, 2), (5, 5)))

    def test_simetria_y_traslacion(self):
        m = calcular_distancias((-3.5, -2), (2, 7.25))
        inversa = calcular_distancias(m.b, m.a)
        trasladada = calcular_distancias((6.5, 8), (12, 17.25))
        self.assertEqual((m.manhattan, m.euclidiana), (inversa.manhattan, inversa.euclidiana))
        self.assertEqual((m.manhattan, m.euclidiana), (trasladada.manhattan, trasladada.euclidiana))
        self.assertLessEqual(m.euclidiana, m.manhattan)

    def test_puntos_iguales_y_alineados(self):
        for a, b in (((2, 2), (2, 2)), ((-4, 3), (8, 3)), ((5, -1), (5, 9))):
            m = calcular_distancias(a, b)
            self.assertEqual(m.manhattan, m.euclidiana)
        self.assertIn('coinciden', conclusion(calcular_distancias((2, 2), (2, 2))))

    def test_ambos_ordenes_miden_lo_mismo(self):
        m = calcular_distancias((5, 6), (-2, -4))
        for orden in ('xy', 'yx'):
            ruta = ruta_manhattan(m, orden)
            self.assertEqual(ruta[0], m.a)
            self.assertEqual(ruta[-1], m.b)
            longitud = 0
            for a, b in zip(ruta, ruta[1:]):
                self.assertTrue(a[0] == b[0] or a[1] == b[1])
                longitud += math.dist(a, b)
            self.assertEqual(longitud, m.manhattan)
        with self.assertRaises(ValueError):
            ruta_manhattan(m, 'diagonal')

    def test_entradas_invalidas(self):
        for punto in ((), (1,), (1, 2, 3), '1,2', None, (True, 1), ('1', 2),
                      (math.nan, 0), (math.inf, 2), (10**400, 1)):
            with self.subTest(punto=repr(punto)[:30]), self.assertRaises(ValueError):
                calcular_distancias(punto, (1, 2))
        with self.assertRaises(ValueError):
            calcular_distancias((-1.7e308, 0), (1.7e308, 0))

    def test_hypot_evade_desbordamiento_de_cuadrados(self):
        m = calcular_distancias((0, 0), (1e154, 1e154))
        self.assertTrue(math.isfinite(m.euclidiana))
        self.assertAlmostEqual(m.euclidiana / 1e154, math.sqrt(2))
        with self.assertRaises(ValueError):
            validar_rango_grafico(m)

    def test_grafica_representa_las_longitudes_y_escala(self):
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        for a, b in (((1, 2), (5, 5)), ((0, 0), (0, 0)), ((1, -2), (1, 5))):
            m = calcular_distancias(a, b)
            fig = crear_figura(m)
            FigureCanvasAgg(fig).draw()
            ax = fig.axes[0]
            self.assertEqual(ax.get_aspect(), 1)
            lineas = {linea.get_gid(): linea for linea in ax.lines}
            for nombre, longitud in (('manhattan', m.manhattan), ('euclidiana', m.euclidiana)):
                puntos = list(zip(*lineas[nombre].get_data()))
                self.assertAlmostEqual(sum(math.dist(x, y) for x, y in zip(puntos, puntos[1:])), longitud)
            self.assertEqual(len(lineas), 2)


if __name__ == '__main__':
    unittest.main()
