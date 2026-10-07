"""Guardar, consultar y reportar con el adaptador MongoDB y un servidor sustituido."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import mongomock
from pymongo.errors import ConnectionFailure
from logismart.dominio.modelos import Configuracion
from logismart.infraestructura.configuracion import datos_mongo
from logismart.infraestructura.repositorio import MongoRepositorio
from logismart.servicios.aplicacion import Aplicacion
from logismart.servicios.clasificador import ClasificadorHibrido
from web.logistica import crear_app, VERSION_SERVIDOR
from test_web import ClienteWeb


class TestDatosMongo(ClienteWeb, unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.mongo = mongomock.MongoClient(tz_aware=True)
        self.repo = MongoRepositorio('mongodb://usuario_prueba:clave_prueba@localhost/', 'examen_prueba', self.mongo)
        self.llm = Mock(modelo='sustituto_de_prueba')
        self.servicio = Aplicacion(self.repo, ClasificadorHibrido(self.llm, False), Configuracion(usar_llm=False))
        self.preparar(crear_app(self.servicio, Path(self.tmp.name), Mock()))

    def guardar_acceso(self, camion='CAM-201', **cambios):
        valores = dict(camion_id=camion, placa='ABC-201-D', P=False, Q=False, R=False,
                       S=True, H=True, T=False)
        return self.api('/registros/accesos', 'POST', {**valores, **cambios}).json['registro']

    def informe(self):
        return self.terminar(self.api('/asistente', 'POST', {
            'pregunta': 'Genera un informe de los camiones que fueron rechazados y sus motivos.'}))

    def test_guardar_en_mongo_y_generar_informe_con_datos_actuales(self):
        estado = self.api('/estado').json
        self.assertIn('informes_accesos_v1', estado['capacidades'])
        self.assertEqual(estado['version_servidor'], VERSION_SERVIDOR)
        self.assertEqual(estado['origen']['base'], 'examen_prueba')
        self.assertEqual(self.api('/asistente/datos').json['colecciones']['accesos'], 0)
        acceso = self.guardar_acceso()
        self.assertIsNotNone(self.mongo.examen_prueba.accesos.find_one({'_id': acceso['_id']}))
        lectura = self.api('/asistente/datos').json
        self.assertEqual(lectura['resultados']['denegado'], 1)
        primero = self.informe()
        self.assertEqual(primero['informe']['total_accesos'], 1)
        self.assertEqual(primero['informe']['origen'], estado['origen'])
        persistido = self.mongo.examen_prueba.evaluaciones_llm.find_one({'_id': primero['_id']})
        self.assertEqual(persistido['informe']['registros'][0]['fuente'], 'accesos:' + acceso['_id'])
        # Una consulta posterior recupera las escrituras nuevas de MongoDB.
        self.guardar_acceso('CAM-202', P=True, S=False)
        self.assertEqual(self.api('/asistente/datos').json['resultados']['denegado'], 2)
        segundo = self.informe()
        self.assertEqual(segundo['informe']['total_accesos'], 2)
        self.assertEqual(self.repo.obtener('evaluaciones_llm', primero['_id'])['informe']['total_accesos'], 1)
        self.llm.chat.assert_not_called()

    def test_lectura_no_cuenta_datos_ajenos_ni_bajas(self):
        acceso = self.guardar_acceso()
        original = self.mongo.examen_prueba.accesos.find_one({'_id': acceso['_id']})
        self.mongo.examen_prueba.accesos.insert_one({**original, '_id': 'otro-alumno', 'alumno': 'Ajeno'})
        self.mongo.examen_prueba.accesos.insert_one({**original, '_id': 'otro-proyecto', 'proyecto': 'Ajeno'})
        self.mongo.examen_prueba.accesos.insert_one({**original, '_id': 'baja', 'eliminado': True})
        datos = self.api('/asistente/datos').json
        self.assertEqual(datos['colecciones']['accesos'], 1)
        self.assertEqual(sum(datos['resultados'].values()), 1)

    def test_error_de_conexion_visible_y_sin_conteos_inventados(self):
        with patch.object(self.repo.db.accesos, 'count_documents', side_effect=ConnectionFailure('fallo simulado')):
            r = self.api('/asistente/datos')
        self.assertEqual(r.status_code, 503)
        self.assertIn('Revisa la conexión', r.json['error'])
        self.assertNotIn('colecciones', r.json)

    def test_metadatos_sin_credenciales(self):
        for ruta in ('/estado', '/asistente/datos'):
            datos = json.dumps(self.api(ruta).json)
            for secreto in ('clave_prueba', 'usuario_prueba', 'mongodb://', 'Mongo_Password'):
                self.assertNotIn(secreto, datos)
        self.assertEqual(self.client.get('/api/asistente/datos').status_code, 403)


class TestArranqueAtlas(unittest.TestCase):
    def test_atlas_no_acepta_el_destino_local_por_defecto(self):
        with patch.dict(os.environ, {'MONGO_URI': 'mongodb://127.0.0.1:27017/'}, clear=True), \
                patch('logismart.infraestructura.configuracion.load_dotenv'):
            with self.assertRaisesRegex(ValueError, 'No se inició MongoDB local'):
                datos_mongo(exigir_atlas=True)

    def test_atlas_construye_uri_sin_necesitar_conexion_en_esta_prueba(self):
        variables = {'Mongo_User': 'usuario_prueba', 'Mongo_Password': 'clave de prueba',
                     'Mongo_Cluster': 'cluster-prueba.mongodb.net', 'Mongo_DB': 'examen_prueba'}
        with patch.dict(os.environ, variables, clear=True), patch('logismart.infraestructura.configuracion.load_dotenv'):
            uri, base = datos_mongo(exigir_atlas=True)
        self.assertTrue(uri.startswith('mongodb+srv://'))
        self.assertIn('clave+de+prueba@', uri)
        self.assertEqual(base, 'examen_prueba')

    def test_atlas_y_demo_son_excluyentes(self):
        from logiuncodigo import crear_servicio
        with patch('logismart.infraestructura.configuracion.cargar_configuracion', return_value=Configuracion()), \
                self.assertRaisesRegex(ValueError, 'no se pueden usar ambos modos'):
            crear_servicio(demo=True, atlas=True)


if __name__ == '__main__':
    unittest.main()
