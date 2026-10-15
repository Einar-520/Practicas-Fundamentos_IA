"""Pruebas de decisiones, restricciones y límites de la búsqueda local."""
from itertools import product
import unittest

from hill_climbing import (
    LISTA, PRODUCTOS, Producto, leer_lista, subir_lista,
    subir_productos, verificar_optimo,
)


class PruebasHillClimbing(unittest.TestCase):
    def test_recorrido_del_ejercicio_y_ambas_direcciones(self):
        resultado = subir_lista()
        self.assertEqual(resultado.recorrido, (2, 5, 8, 12))
        self.assertEqual(len(resultado.indices) - 1, 3)
        self.assertEqual(subir_lista(LISTA, 6).recorrido, (3, 6, 9, 12))
        self.assertEqual(subir_lista(LISTA, 3).recorrido, (12,))

    def test_maximo_local_meseta_y_empate(self):
        self.assertEqual(subir_lista((2, 5, 4, 12)).recorrido, (2, 5))
        self.assertEqual(subir_lista((2, 2, 8)).recorrido, (2,))
        self.assertEqual(subir_lista((8, 2, 8), 1).indices, (1, 0))
        self.assertEqual(subir_lista((-4,)).valor_final, -4)

    def test_productos_del_profesor(self):
        resultado = subir_productos()
        self.assertEqual([s.productos for s in resultado.pasos], [(), ('C',), ('C', 'E'), ('C', 'D', 'E')])
        self.assertEqual((resultado.final.costo, resultado.final.beneficio), (1000, 170))
        exacta = verificar_optimo()
        self.assertEqual(exacta.combinaciones, 32)
        self.assertEqual(exacta.factibles, 25)
        self.assertEqual(exacta.soluciones, (resultado.final,))

    def test_maximo_local_con_el_mismo_catalogo(self):
        resultado = subir_productos(presupuesto=850)
        exacta = verificar_optimo(presupuesto=850)
        self.assertEqual((resultado.final.productos, resultado.final.beneficio), (('C', 'E'), 130))
        self.assertEqual(exacta.beneficio, 140)
        self.assertEqual([s.productos for s in exacta.soluciones], [('A', 'B', 'E'), ('A', 'C', 'D')])
        # Los intercambios no se confunden con movimientos que empeoran primero.
        atrapado = (Producto('X', 1000, 60), Producto('Y', 500, 40), Producto('Z', 500, 40))
        self.assertEqual(subir_productos(atrapado).final.beneficio, 60)
        self.assertEqual(verificar_optimo(atrapado).beneficio, 80)

    def test_presupuesto_y_mejora_estricta_desde_todas_las_selecciones(self):
        # Oráculo independiente: máscaras binarias, sin usar el generador de vecinos.
        estados = []
        for bits in product((0, 1), repeat=5):
            grupo = tuple(p for p, bit in zip(PRODUCTOS, bits) if bit)
            estados.append((tuple(p.nombre for p in grupo), sum(p.costo for p in grupo), sum(p.beneficio for p in grupo)))
        for presupuesto in (0, 199, 200, 600, 850, 1000, 1500):
            factibles = [e for e in estados if e[1] <= presupuesto]
            esperado = max(e[2] for e in factibles)
            exacta = verificar_optimo(presupuesto=presupuesto)
            self.assertEqual(exacta.beneficio, esperado)
            self.assertEqual({s.productos for s in exacta.soluciones}, {e[0] for e in factibles if e[2] == esperado})
            for inicio, _, _ in factibles:
                resultado = subir_productos(presupuesto=presupuesto, inicio=inicio)
                self.assertLessEqual(resultado.final.beneficio, esperado)
                for anterior, siguiente in zip(resultado.pasos, resultado.pasos[1:]):
                    self.assertGreater(siguiente.beneficio, anterior.beneficio)
                    self.assertLessEqual(siguiente.costo, presupuesto)
                    self.assertLessEqual(len(set(anterior.productos) - set(siguiente.productos)), 1)
                    self.assertLessEqual(len(set(siguiente.productos) - set(anterior.productos)), 1)
                final = set(resultado.final.productos)
                for grupo, costo, beneficio in factibles:
                    if len(final - set(grupo)) <= 1 and len(set(grupo) - final) <= 1:
                        self.assertLessEqual(beneficio, resultado.final.beneficio)

    def test_validacion_de_lista(self):
        for lista, inicio in (((), 0), ((float('nan'),), 0), ((float('inf'),), 0), ((True,), 0), (LISTA, -1), (LISTA, 7)):
            with self.subTest(lista=lista, inicio=inicio), self.assertRaises(ValueError):
                subir_lista(lista, inicio)
        for texto in ('', 'dos, 5', '2,,5', 'nan, 2', 'inf', '1000001', ','.join(['1'] * 41)):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                leer_lista(texto)
        self.assertEqual(leer_lista('-2, 5.5'), (-2, 5.5))

    def test_validacion_de_catalogo_presupuesto_y_seleccion(self):
        for presupuesto in (-1, 2.5, True):
            with self.subTest(presupuesto=presupuesto), self.assertRaises(ValueError):
                subir_productos(presupuesto=presupuesto)
        for inicio in (('Z',), ('A', 'A'), ('A', 'B', 'C', 'D', 'E')):
            with self.subTest(inicio=inicio), self.assertRaises(ValueError):
                subir_productos(inicio=inicio)
        for catalogo in ((), (Producto('A', 0, 3),), (Producto('A', 1, -1),), (PRODUCTOS[0], PRODUCTOS[0])):
            with self.subTest(catalogo=catalogo), self.assertRaises(ValueError):
                subir_productos(catalogo)


if __name__ == '__main__':
    unittest.main()
