"""Invariantes del calendario, equidad y exportación de los mismos datos."""
import csv
from itertools import permutations
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from asignacion import EMPLEADOS, INICIO, TURNOS, puntuar, verificar_optimas
from rotacion import generar_rotacion, guardar_csv


class PruebasRotacion(unittest.TestCase):
    def test_rotacion_completa_desde_cualquier_base(self):
        for base in permutations(TURNOS):
            calendario = generar_rotacion(base, 8)
            self.assertEqual(calendario.periodos[0].asignacion, base)
            self.assertEqual(calendario.periodos[4].asignacion, base)
            self.assertEqual(calendario.cumplimientos, (2, 2, 2, 2))
            self.assertEqual(calendario.porcentaje, 25)
            for inicio in (0, 4):
                for empleado in range(4):
                    self.assertEqual({p.asignacion[empleado] for p in calendario.periodos[inicio:inicio+4]}, set(TURNOS))
            for anterior, siguiente in zip(calendario.periodos, calendario.periodos[1:]):
                self.assertTrue(all(a != b for a, b in zip(anterior.asignacion, siguiente.asignacion)))

    def test_alternancia_conserva_maximo_y_reparte_manana(self):
        for base in verificar_optimas().asignaciones:
            calendario = generar_rotacion(base, 4, "preferencias")
            self.assertEqual(calendario.cumplimientos, (2, 4, 4, 2))
            self.assertEqual(calendario.porcentaje, 75)
            for i, periodo in enumerate(calendario.periodos):
                self.assertEqual(periodo.satisfaccion, 3)
                self.assertEqual(periodo.asignacion[1:3], ("Tarde", "Noche"))
                self.assertEqual(periodo.asignacion[0], base[0 if i % 2 == 0 else 3])

    def test_calendarios_cortos_impares_y_largos(self):
        base = verificar_optimas().asignaciones[0]
        for cantidad in (1, 3, 4, 5, 52):
            for modo in ("completa", "preferencias"):
                calendario = generar_rotacion(base, cantidad, modo)
                self.assertEqual(len(calendario.periodos), cantidad)
                for i, periodo in enumerate(calendario.periodos, 1):
                    self.assertEqual(periodo.numero, i)
                    self.assertEqual(set(periodo.asignacion), set(TURNOS))
                    self.assertEqual(periodo.satisfaccion, puntuar(periodo.asignacion))

    def test_rechaza_entradas_invalidas(self):
        for cantidad in (0, -1, 53, 1.5, True, "4"):
            with self.assertRaises(ValueError):
                generar_rotacion(INICIO, cantidad)
        for base, modo in ((INICIO, "otro"), (("Mañana",)*4, "completa"), (INICIO, "preferencias")):
            with self.assertRaises(ValueError):
                generar_rotacion(base, modo=modo)

    def test_csv_preserva_nombres_y_resultados(self):
        calendario = generar_rotacion(verificar_optimas().asignaciones[0], 5)
        with TemporaryDirectory() as temporal:
            archivo = guardar_csv(calendario, Path(temporal)/"subcarpeta"/"turnos.csv")
            with archivo.open(encoding="utf-8-sig", newline="") as entrada:
                filas = list(csv.reader(entrada))
            self.assertEqual(filas[0][1:5], list(EMPLEADOS))
            self.assertEqual(len(filas), 6)
            for fila, periodo in zip(filas[1:], calendario.periodos):
                self.assertEqual(fila[1:5], list(periodo.asignacion))
                self.assertEqual(int(fila[5]), periodo.satisfaccion)
                self.assertEqual(fila[6], f"{periodo.satisfaccion / 4:.0%}")


if __name__ == "__main__":
    unittest.main()
