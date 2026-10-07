"""Informes agrupados: filtros, causas, trazabilidad y ámbito de MongoDB."""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import mongomock
from logismart.dominio.modelos import Configuracion
from logismart.infraestructura.repositorio import DemoRepositorio, MongoRepositorio, ErrorDatos
from logismart.servicios.aplicacion import Aplicacion
from logismart.servicios.asistente import responder
from logismart.servicios.clasificador import ClasificadorHibrido
from logismart.servicios.demostracion import cargar_demo
from logismart.servicios.informes_accesos import construir_informe, filtros_desde_pregunta, texto_informe


class TestInformes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = DemoRepositorio(Path(self.tmp.name) / 'prueba.json')
        self.llm = Mock(modelo='sustituto_prueba')
        self.app = Aplicacion(self.repo, ClasificadorHibrido(self.llm, False), Configuracion(usar_llm=False))
        cargar_demo(self.app)

    def test_prompt_de_la_captura_y_motivos_concretos_sin_llm(self):
        r = responder(self.repo, self.llm, 'Genera un informe de los camiones que fueron rechazados y '
                      'los motivos del por que', 'Prueba', usar_llm=True)
        self.assertEqual(r['informe']['total_accesos'], 2)
        self.assertEqual(r['informe']['camiones_unicos'], 2)
        motivos = {a['camion_id']: a['motivos'] for a in r['informe']['registros']}
        self.assertEqual(motivos['CAM-103'], ['Falta de autorización previa (P=False).'])
        self.assertEqual(motivos['CAM-104'], ['Certificación del conductor no vigente (S=False).'])
        self.assertIn('informe_registros', r['estado'])
        self.assertFalse(r['llm_consultado'])
        self.llm.chat.assert_not_called()
        self.assertEqual(self.repo.obtener('evaluaciones_llm', r['_id'])['informe'], r['informe'])

    def test_cuenta_todos_los_accesos_y_no_duplica_camiones(self):
        for _ in range(21):
            self.app.guardar_acceso(dict(camion_id='CAM-103', placa='ABC-103-D',
                                        P=False, Q=False, R=False, S=False, H=True, T=False))
        informe = construir_informe(self.repo, 'denegado')
        self.assertEqual(informe['total_accesos'], 23)
        self.assertEqual(informe['camiones_unicos'], 2)
        self.assertEqual(sum(informe['resumen_motivos'].values()), 44)
        self.assertIn('23 accesos', texto_informe(informe))
        self.assertEqual(len(informe['registros']), 23)

    def test_retenidos_no_se_mezclan_con_rechazados(self):
        self.app.guardar_acceso(dict(camion_id='CAM-101', placa='ABC-101-D',
                                    P=True, Q=False, R=True, S=True, H=False, T=True))
        self.assertEqual(construir_informe(self.repo, 'denegado')['total_accesos'], 2)
        informe = construir_informe(self.repo, 'retenido')
        self.assertEqual(informe['total_accesos'], 1)
        self.assertEqual(len(informe['registros'][0]['motivos']), 2)

    def test_periodo_y_camion_sin_coincidencias(self):
        filtros = filtros_desde_pregunta('Informe de accesos rechazados de CAM-103 desde 2000-01-01 hasta 2000-12-31')
        informe = construir_informe(self.repo, **filtros)
        self.assertEqual(informe['total_accesos'], 0)
        self.assertIn('No hay registros', texto_informe(informe))
        self.assertEqual(filtros['camion_id'], 'CAM-103')

    def test_fecha_utc_incluye_fin_del_dia_y_excluye_el_siguiente(self):
        accesos = self.repo.datos['accesos']
        accesos[0]['creado_en'] = '2026-10-07T23:59:59+00:00'
        for acceso in accesos[1:]:
            acceso['creado_en'] = '2026-10-08T00:00:00+00:00'
        r = construir_informe(self.repo, desde='2026-10-07', hasta='2026-10-07')
        self.assertEqual(r['total_accesos'], 1)

    def test_filtros_permitidos_y_consulta_individual(self):
        for texto, resultado in [('Informe de camiones rechazados', 'denegado'),
                                 ('Cuáles camiones están en inspección', 'inspeccion'),
                                 ('Informe de camiones autorizados', 'autorizado'),
                                 ('Lista de todos los accesos', 'todos')]:
            self.assertEqual(filtros_desde_pregunta(texto)['resultado'], resultado)
        self.assertIsNone(filtros_desde_pregunta('¿Por qué CAM-102 fue a inspección?'))
        self.assertEqual(filtros_desde_pregunta('Informe de camiones rechazados hoy')['desde'],
                         datetime.now(timezone.utc).date().isoformat())

    def test_rechaza_periodos_ambiguos_y_filtros_no_permitidos(self):
        for texto in ['en octubre', 'ayer y hoy', 'en los últimos siete días', 'desde 07/10/2026',
                      'desde 2026-11-30 hasta 2026-11-01', 'el 2026-02-30', 'por empresa',
                      'excepto CAM-101', 'y retenidos', 'desde', 'CAM-101 y CAM-102']:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                filtros_desde_pregunta('Informe de camiones rechazados ' + texto)
        with self.assertRaises(ValueError):
            construir_informe(self.repo, resultado='$where')

    def test_informe_demasiado_grande_pide_periodo_no_recorta(self):
        with patch('logismart.servicios.informes_accesos.MAX_REGISTROS', 1), self.assertRaisesRegex(ValueError, 'Reduce el período'):
            construir_informe(self.repo, 'denegado')

    def test_error_de_conexion_no_se_presenta_como_informe_vacio(self):
        self.repo.listar = Mock(side_effect=ErrorDatos('No se pudieron consultar los registros.'))
        with self.assertRaises(ErrorDatos):
            responder(self.repo, self.llm, 'Informe de camiones rechazados', 'Prueba')

    def test_mongodb_excluye_registros_ajenos_y_bajas(self):
        repo = MongoRepositorio('mongodb://localhost/', 'prueba_informe', mongomock.MongoClient(tz_aware=True))
        servicio = Aplicacion(repo, ClasificadorHibrido(self.llm, False), Configuracion(usar_llm=False))
        cargar_demo(servicio)
        original = repo.db.accesos.find_one({'resultado': 'denegado'})
        repo.db.accesos.insert_one({**original, '_id': 'otro-alumno', 'alumno': 'Ajeno'})
        repo.db.accesos.insert_one({**original, '_id': 'eliminado', 'eliminado': True})
        r = construir_informe(repo, 'denegado')
        self.assertEqual(r['total_accesos'], 2)
        self.assertFalse({'accesos:otro-alumno', 'accesos:eliminado'} & {a['fuente'] for a in r['registros']})


if __name__ == '__main__':
    unittest.main()
