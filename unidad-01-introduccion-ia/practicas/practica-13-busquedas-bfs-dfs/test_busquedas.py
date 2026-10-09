"""Regresiones de rutas, ciclos, retrocesos y validación de búsquedas."""
import unittest

from busquedas import GRAFO_BFS, GRAFO_DFS, bfs, dfs


class PruebasBusqueda(unittest.TestCase):
    def test_bfs_original(self):
        resultado = bfs(GRAFO_BFS)
        self.assertEqual(resultado.ruta, ("A", "B", "C", "F"))
        self.assertEqual(resultado.orden, ("A", "B", "D", "C", "E", "F"))
        self.assertEqual(resultado.costo, 3)

    def test_dfs_original_y_retroceso(self):
        resultado = dfs(GRAFO_DFS)
        self.assertEqual(resultado.ruta, ("A", "C", "F"))
        self.assertEqual(resultado.orden, ("A", "B", "D", "E", "C", "F"))
        self.assertEqual(resultado.costo, 2)
        self.assertEqual([p.camino for p in resultado.pasos if p.evento == "Retroceso"],
                         [("A", "B"), ("A", "B"), ("A",)])

    def test_bfs_corto_dfs_primera_rama_en_mismo_grafo(self):
        grafo = {"S": ["A", "T"], "A": ["B"], "B": ["T"], "T": []}
        self.assertEqual(bfs(grafo, "S", "T").ruta, ("S", "T"))
        self.assertEqual(dfs(grafo, "S", "T").ruta, ("S", "A", "B", "T"))

    def test_ciclo_y_nodo_aislado(self):
        grafo = {"A": ["A", "B"], "B": ["A"], "C": []}
        for buscar in (bfs, dfs):
            with self.subTest(buscar=buscar.__name__):
                resultado = buscar(grafo, "A", "C")
                self.assertIsNone(resultado.ruta)
                self.assertIsNone(resultado.costo)
                self.assertEqual(resultado.orden, ("A", "B"))
                self.assertEqual(resultado.pasos[-1].camino, ())
                self.assertEqual(resultado.pasos[-1].evento, "Sin ruta")

    def test_inicio_es_meta(self):
        for buscar in (bfs, dfs):
            resultado = buscar(GRAFO_BFS, "A", "A")
            self.assertEqual(resultado.ruta, ("A",))
            self.assertEqual(resultado.costo, 0)
            self.assertEqual(resultado.orden, ("A",))

    def test_entradas_invalidas(self):
        for buscar in (bfs, dfs):
            for grafo, inicio, meta in (({}, "A", "A"), (GRAFO_BFS, "Z", "F"),
                                        (GRAFO_DFS, "A", "Z"), ({"A": ["Z"]}, "A", "A"),
                                        ({"A": {"A"}}, "A", "A")):
                with self.subTest(buscar=buscar.__name__, grafo=grafo, inicio=inicio, meta=meta):
                    with self.assertRaises(ValueError):
                        buscar(grafo, inicio, meta)

    def test_repetir_no_contamina_estado(self):
        for buscar, grafo in ((bfs, GRAFO_BFS), (dfs, GRAFO_DFS)):
            copia = {nodo: vecinos[:] for nodo, vecinos in grafo.items()}
            primero = buscar(grafo)
            buscar(grafo, "F", "A")
            self.assertEqual(buscar(grafo), primero)
            self.assertEqual(grafo, copia)
            self.assertEqual(primero.pasos[0].camino, ("A",))


if __name__ == "__main__":
    unittest.main()
