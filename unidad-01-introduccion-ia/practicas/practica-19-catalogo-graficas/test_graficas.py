"""Verifica los errores visuales corregidos y la independencia de los ejemplos."""
import unittest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from datos import generar_datos
from graficas import CATALOGO
from paletas import PALETAS, estilo


class PruebasGraficas(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_ranking_ordenado_y_colores_consistentes(self):
        datos = generar_datos()
        for paleta in PALETAS.values():
            eje = CATALOGO[4][3](datos, paleta).axes[0]
            self.assertEqual([t.get_text() for t in eje.get_yticklabels()],
                             ["Mouse", "Teclado", "Audífonos", "Laptop", "Monitor"])
            self.assertEqual([b.get_width() for b in eje.patches], [210, 180, 145, 120, 95])
            color_mouse = matplotlib.colors.to_rgba(paleta.categorias[3])
            self.assertEqual(eje.patches[0].get_facecolor(), color_mouse)

    def test_porcentajes_dentro_del_anillo(self):
        for paleta in PALETAS.values():
            eje = CATALOGO[10][3](generar_datos(), paleta).axes[0]
            porcentajes = [texto for texto in eje.texts if texto.get_text().endswith("%")]
            self.assertEqual({t.get_text() for t in porcentajes}, {"40.0%", "30.0%", "20.0%", "10.0%"})
            for texto in porcentajes:
                radio = np.hypot(*texto.get_position())
                self.assertGreater(radio, .58)
                self.assertLess(radio, 1)

    def test_ejemplos_independientes_en_orden_inverso(self):
        datos = generar_datos()
        paleta = PALETAS["original"]
        with plt.rc_context(estilo(paleta)):
            for numero in reversed(CATALOGO):
                with self.subTest(numero=numero):
                    figura = CATALOGO[numero][3](datos, paleta)
                    figura.canvas.draw()
                    self.assertTrue(figura.axes)
                    plt.close(figura)


if __name__ == "__main__":
    unittest.main()
