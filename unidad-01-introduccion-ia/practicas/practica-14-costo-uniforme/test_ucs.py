"""Casos que distinguen UCS de BFS y de una búsqueda voraz por arista."""
import unittest

from busqueda_ucs import GRAFO_ORIGINAL, ucs


class PruebasUCS(unittest.TestCase):
    def test_ruta_y_costos_del_pizarron(self):
        resultado = ucs(GRAFO_ORIGINAL)
        self.assertEqual(resultado.ruta, ("A", "C", "F", "J"))
        self.assertEqual(resultado.costo, 8)
        self.assertEqual(resultado.orden, ("A", "B", "C", "E", "F", "I", "D", "J"))
        self.assertEqual([p.costo for p in resultado.pasos], [0, 2, 3, 3, 5, 5, 6, 8])
        self.assertEqual(resultado.pasos[-1].profundidad, 3)
        for meta, costo in (("H", 9), ("I", 5), ("G", 9)):
            self.assertEqual(ucs(GRAFO_ORIGINAL, "A", meta).costo, costo)

    def test_no_termina_al_descubrir_la_meta(self):
        grafo = {"A": {"T": 10, "B": 1}, "B": {"T": 1}, "T": {}}
        resultado = ucs(grafo, "A", "T")
        self.assertEqual(resultado.ruta, ("A", "B", "T"))
        self.assertEqual(resultado.costo, 2)

    def test_usa_acumulado_no_solo_ultima_arista(self):
        grafo = {"A": {"B": 1, "C": 3}, "B": {"T": 100}, "C": {"T": 2}, "T": {}}
        resultado = ucs(grafo, "A", "T")
        self.assertEqual(resultado.ruta, ("A", "C", "T"))
        self.assertEqual(resultado.costo, 5)

    def test_descarta_entradas_antiguas(self):
        grafo = {"A": {"B": 9, "C": 1}, "C": {"B": 1}, "B": {"T": 20}, "T": {}}
        resultado = ucs(grafo, "A", "T")
        self.assertEqual(resultado.ruta, ("A", "C", "B", "T"))
        self.assertEqual(resultado.costo, 22)
        self.assertEqual(resultado.orden, ("A", "C", "B", "T"))
        self.assertEqual([a.costo for a in resultado.pasos[1].frontera], [2])

    def test_empate_respeta_orden_de_insercion(self):
        grafo = {"A": {"Z": 1, "B": 1}, "Z": {"T": 1}, "B": {"T": 1}, "T": {}}
        resultado = ucs(grafo, "A", "T")
        self.assertEqual(resultado.ruta, ("A", "Z", "T"))
        self.assertEqual(resultado.orden, ("A", "Z", "B", "T"))

    def test_ciclo_de_costo_cero_no_se_repite(self):
        grafo = {"A": {"B": 0}, "B": {"A": 0, "T": 2}, "T": {}}
        resultado = ucs(grafo, "A", "T")
        self.assertEqual(resultado.orden, ("A", "B", "T"))
        self.assertEqual(resultado.costo, 2)

    def test_sin_ruta_e_inicio_igual_a_meta(self):
        resultado = ucs(GRAFO_ORIGINAL, "J", "A")
        self.assertIsNone(resultado.ruta)
        self.assertIsNone(resultado.costo)
        self.assertEqual(resultado.pasos[-1].evento, "Sin ruta")
        resultado = ucs(GRAFO_ORIGINAL, "J", "J")
        self.assertEqual(resultado.ruta, ("J",))
        self.assertEqual(resultado.costo, 0)

    def test_rechaza_costos_invalidos_y_estados_ausentes(self):
        for costo in (-1, float("nan"), float("inf"), True, "dos", 10 ** 400):
            with self.subTest(costo=str(costo)[:20]):
                with self.assertRaises(ValueError):
                    ucs({"A": {"B": costo}, "B": {}}, "A", "B")
        for grafo, inicio, meta in (({}, "A", "J"), (GRAFO_ORIGINAL, "Z", "J"),
                                    ({"A": {"Z": 1}}, "A", "A"), ({"A": []}, "A", "A")):
            with self.assertRaises(ValueError):
                ucs(grafo, inicio, meta)

    def test_rechaza_desbordamiento_del_acumulado(self):
        with self.assertRaises(ValueError):
            ucs({"A": {"B": 1e308}, "B": {"C": 1e308}, "C": {}}, "A", "C")

    def test_frontera_ordenada_y_ejecuciones_independientes(self):
        copia = {nodo: dict(vecinos) for nodo, vecinos in GRAFO_ORIGINAL.items()}
        primero = ucs(GRAFO_ORIGINAL)
        ucs(GRAFO_ORIGINAL, "A", "H")
        self.assertEqual(primero, ucs(GRAFO_ORIGINAL))
        self.assertEqual(GRAFO_ORIGINAL, copia)
        for paso in primero.pasos:
            costos = [alternativa.costo for alternativa in paso.frontera]
            self.assertEqual(costos, sorted(costos))
            self.assertTrue(all(a.estado not in paso.visitados for a in paso.frontera))


if __name__ == "__main__":
    unittest.main()
