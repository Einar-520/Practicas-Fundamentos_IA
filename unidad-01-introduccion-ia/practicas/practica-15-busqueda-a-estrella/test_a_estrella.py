"""Pruebas del recorrido, prioridad f, reapertura y validación de A*."""
import copy
import math
import unittest

from busqueda_a_estrella import (
    GRAFO_ORIGINAL, HEURISTICA_ORIGINAL, a_estrella,
    analizar_heuristica, validar_problema,
)


class PruebasAEstrella(unittest.TestCase):
    def test_ejercicio_del_profesor(self):
        r = a_estrella(GRAFO_ORIGINAL, HEURISTICA_ORIGINAL)
        self.assertEqual(r.ruta, ("A", "C", "F", "I", "J"))
        self.assertEqual(r.costo, 4)
        self.assertEqual(r.orden, r.ruta)
        self.assertEqual([(p.g, p.h, p.f) for p in r.pasos],
                         [(0, 7, 7), (1, 4, 5), (2, 3, 5), (3, 1, 4), (4, 0, 4)])
        self.assertEqual([(a.estado, a.f) for a in r.pasos[0].frontera], [("C", 5), ("B", 7)])
        self.assertEqual([(a.estado, a.f) for a in r.pasos[-1].frontera], [("B", 7), ("G", 8)])
        self.assertEqual(r.pasos[-1].profundidad, 4)
        self.assertEqual(GRAFO_ORIGINAL['F'], {'I': 1})
        self.assertEqual(GRAFO_ORIGINAL['I'], {'J': 1})
        self.assertEqual(GRAFO_ORIGINAL['E'], {})

    def test_prioridad_por_f_no_solo_g_o_h(self):
        grafo = {"S": {"A": 1, "B": 2}, "A": {"T": 10}, "B": {"T": 2}, "T": {}}
        r = a_estrella(grafo, {"S": 0, "A": 4, "B": 0, "T": 0}, "S", "T")
        self.assertEqual(r.orden, ("S", "B", "T"))
        self.assertEqual(r.costo, 4)
        # Una heurística baja tampoco basta si g hace que f sea mayor.
        grafo = {"S": {"A": 1, "B": 8}, "A": {"T": 3}, "B": {"T": 1}, "T": {}}
        r = a_estrella(grafo, {"S": 0, "A": 3, "B": 0, "T": 0}, "S", "T")
        self.assertEqual(r.ruta, ("S", "A", "T"))

    def test_meta_al_extraer_no_al_descubrir(self):
        r = a_estrella({"S": {"T": 10, "B": 1}, "B": {"T": 1}, "T": {}},
                       {"S": 0, "B": 1, "T": 0}, "S", "T")
        self.assertEqual(r.ruta, ("S", "B", "T"))
        self.assertEqual(r.costo, 2)

    def test_reabre_estado_con_mejor_g(self):
        grafo = {"S": {"A": 3, "B": 1}, "A": {"T": 3}, "B": {"A": 1}, "T": {}}
        h = {"S": 0, "A": 0, "B": 3, "T": 0}  # Admisible, pero inconsistente.
        r = a_estrella(grafo, h, "S", "T")
        self.assertEqual(r.orden, ("S", "A", "B", "A", "T"))
        self.assertEqual(r.pasos[3].evento, "Reexplorar")
        self.assertEqual(r.ruta, ("S", "B", "A", "T"))
        self.assertEqual(r.costo, 5)
        self.assertTrue(analizar_heuristica(grafo, h, "T").admisible)

    def test_descarta_entradas_antiguas(self):
        grafo = {"S": {"A": 5, "B": 1}, "A": {"T": 10}, "B": {"A": 1}, "T": {}}
        r = a_estrella(grafo, dict.fromkeys(grafo, 0), "S", "T")
        self.assertEqual(r.orden, ("S", "B", "A", "T"))
        self.assertEqual(r.costo, 12)
        for paso in r.pasos:
            self.assertEqual(len({a.estado for a in paso.frontera}), len(paso.frontera))
            self.assertEqual([a.f for a in paso.frontera], sorted(a.f for a in paso.frontera))

    def test_empates_por_llegada(self):
        grafo = {"S": {"Z": 1, "A": 1}, "Z": {"T": 1}, "A": {"T": 1}, "T": {}}
        r = a_estrella(grafo, dict.fromkeys(grafo, 0), "S", "T")
        self.assertEqual(r.orden, ("S", "Z", "A", "T"))
        self.assertEqual(r.ruta, ("S", "Z", "T"))

    def test_ciclo_de_costo_cero(self):
        grafo = {"S": {"A": 0}, "A": {"S": 0, "T": 2}, "T": {}}
        r = a_estrella(grafo, dict.fromkeys(grafo, 0), "S", "T")
        self.assertEqual(r.orden, ("S", "A", "T"))
        self.assertEqual(r.costo, 2)

    def test_sin_ruta_e_inicio_igual_meta(self):
        grafo = {"S": {}, "T": {}}
        r = a_estrella(grafo, dict.fromkeys(grafo, 0), "S", "T")
        self.assertIsNone(r.ruta)
        self.assertIsNone(r.costo)
        self.assertEqual(r.pasos[-1].evento, "Sin ruta")
        self.assertIsNone(r.pasos[-1].f)
        r = a_estrella(grafo, dict.fromkeys(grafo, 0), "T", "T")
        self.assertEqual((r.ruta, r.costo), (("T",), 0))

    def test_revision_de_heuristicas(self):
        d = analizar_heuristica(GRAFO_ORIGINAL, HEURISTICA_ORIGINAL)
        self.assertEqual(d.sobreestimados, ("A", "C", "F"))
        self.assertEqual(d.inconsistencias, (("A", "C"), ("F", "I")))
        self.assertEqual([d.distancias[n] for n in ("A", "C", "F", "I", "J")], [4, 3, 2, 1, 0])
        self.assertTrue(math.isinf(d.distancias["B"]))
        self.assertFalse(d.admisible)
        h = dict.fromkeys(GRAFO_ORIGINAL, 0)
        self.assertTrue(analizar_heuristica(GRAFO_ORIGINAL, h).admisible)
        r = a_estrella(GRAFO_ORIGINAL, h)
        self.assertEqual(r.orden, tuple("ABCDEFGHIJ"))
        self.assertEqual(r.costo, 4)

    def test_sobreestimar_puede_dar_ruta_suboptima(self):
        grafo = {"S": {"A": 1, "T": 5}, "A": {"T": 1}, "T": {}}
        h = {"S": 0, "A": 10, "T": 0}
        self.assertFalse(analizar_heuristica(grafo, h, "T").admisible)
        self.assertEqual(a_estrella(grafo, h, "S", "T").costo, 5)
        self.assertEqual(a_estrella(grafo, dict.fromkeys(grafo, 0), "S", "T").costo, 2)

    def test_validacion(self):
        for valor in (-1, math.inf, math.nan, True, "2", None, 10**400):
            with self.subTest(valor=repr(valor)[:20]):
                with self.assertRaises(ValueError):
                    a_estrella({"A": {"J": valor}, "J": {}}, {"A": 0, "J": 0})
                with self.assertRaises(ValueError):
                    a_estrella({"A": {"J": 1}, "J": {}}, {"A": valor, "J": 0})
        for grafo, h in (({}, {}), ({"A": []}, {"A": 0}),
                         ({"A": {"X": 1}, "J": {}}, {"A": 0, "J": 0}),
                         ({"A": {"J": 1}, "J": {}}, {"A": 0}),
                         ({"A": {"J": 1}, "J": {}}, {"A": 0, "J": 1}),
                         ({"A": {}, "J": {}}, {"A": 0, "J": 0, "X": 1})):
            with self.assertRaises(ValueError):
                validar_problema(grafo, h)
        with self.assertRaises(ValueError):
            a_estrella(GRAFO_ORIGINAL, HEURISTICA_ORIGINAL, [], "J")

    def test_desbordamientos_y_datos_sin_mutar(self):
        for grafo, h in (({"A": {"B": 1.7e308}, "B": {"J": 1.7e308}, "J": {}}, {"A": 0, "B": 0, "J": 0}),
                         ({"A": {"B": 1.7e308}, "B": {"J": 1}, "J": {}}, {"A": 0, "B": 1.7e308, "J": 0})):
            with self.assertRaises(ValueError):
                a_estrella(grafo, h)
        copia = copy.deepcopy((GRAFO_ORIGINAL, HEURISTICA_ORIGINAL))
        a_estrella(GRAFO_ORIGINAL, HEURISTICA_ORIGINAL)
        analizar_heuristica(GRAFO_ORIGINAL, HEURISTICA_ORIGINAL)
        self.assertEqual((GRAFO_ORIGINAL, HEURISTICA_ORIGINAL), copia)


if __name__ == "__main__":
    unittest.main()
