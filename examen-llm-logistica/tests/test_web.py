"""Flujos HTTP reales con persistencia temporal y un sustituto explícito de Ollama."""
import json
import re
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

from comun.ollama_local import ErrorLLM
from logismart.dominio.modelos import Configuracion
from logismart.infraestructura.repositorio import DemoRepositorio
from logismart.servicios.aplicacion import Aplicacion
from logismart.servicios.clasificador import ClasificadorHibrido
from logismart.servicios.demostracion import cargar_demo
from tutor.servicio import TutorSQL
from web.logistica import crear_app
from web.tutor import crear_app as crear_tutor


class ClienteWeb:
    def preparar(self, app):
        self.app = app
        self.client = app.test_client()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.headers = {'X-CSRF-Token': re.search(r'name="csrf-token" content="([^"]+)"', response.text)[1]}

    def api(self, path, method='GET', data=None):
        return self.client.open('/api' + path, method=method, json=data, headers=self.headers)

    def terminar(self, respuesta):
        self.assertEqual(respuesta.status_code, 202, respuesta.text)
        identificador = respuesta.json['trabajo']
        limite = time.monotonic() + 5
        while time.monotonic() < limite:
            resultado = self.api('/trabajos/' + identificador).json
            if resultado['estado'] != 'en_proceso':
                self.assertEqual(resultado['estado'], 'completado', resultado)
                return resultado['resultado']
            time.sleep(.005)
        self.fail('El trabajo no terminó en cinco segundos.')


class TestWebLogistica(ClienteWeb, unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = DemoRepositorio(Path(self.tmp.name) / 'datos.json')
        self.llm = Mock(modelo='sustituto_de_prueba')
        self.servicio = Aplicacion(self.repo, ClasificadorHibrido(self.llm, False), Configuracion(usar_llm=False))
        cargar_demo(self.servicio)
        self.guardar = Mock()
        self.preparar(crear_app(self.servicio, Path(self.tmp.name), self.guardar))

    def test_pagina_y_archivos_locales(self):
        self.assertIn('Panel de control', self.client.get('/').text)
        for ruta in ('comun.js', 'logistica.js', 'estilos.css', 'marca.svg'):
            with self.client.get('/static/' + ruta) as respuesta:
                self.assertEqual(respuesta.status_code, 200)
        self.assertIn("script-src 'self'", self.client.get('/').headers['Content-Security-Policy'])

    def test_protege_origen_host_y_csrf(self):
        self.assertEqual(self.client.get('/api/estado').status_code, 403)
        self.assertEqual(self.client.get('/api/estado', headers={**self.headers, 'Sec-Fetch-Site': 'cross-site'}).status_code, 403)
        self.assertEqual(self.client.get('/', headers={'Host': 'sitio-ajeno.example'}).status_code, 400)
        self.assertNotIn('Mongo_Password', json.dumps(self.api('/estado').json))

    def test_panel_y_periodo(self):
        data = self.api('/panel').json
        self.assertEqual(data['camiones_atendidos'], 4)
        self.assertEqual(sum(data['distribucion'].values()), data['accesos'])
        self.assertEqual(self.api('/panel?desde=2000-01-01&hasta=2001-01-01').json['accesos'], 0)
        self.assertEqual(self.api('/panel?desde=texto').status_code, 400)

    def test_crud_camion_historial_version_y_baja(self):
        datos = dict(camion_id='CAM-222', placa='XYZ-222-D', empresa='Empresa web', autorizacion=True,
                     certificacion_conductor=True, certificado_id='C222', certificacion_hasta='2035-12-31')
        r = self.api('/registros/camiones', 'POST', datos)
        self.assertEqual(r.status_code, 200, r.text)
        registro = r.json['registro']
        cambio = {**datos, 'id': registro['_id'], 'version': 1, 'empresa': 'Empresa corregida'}
        editado = self.api('/registros/camiones', 'POST', cambio).json['registro']
        self.assertEqual(editado['historico'][-1]['anterior']['empresa'], 'Empresa web')
        self.assertEqual(self.api('/registros/camiones', 'POST', cambio).status_code, 400)
        ruta = '/registros/camiones/' + registro['_id']
        self.assertEqual(self.api(ruta, 'DELETE', {'confirmar': False, 'version': 2}).status_code, 400)
        self.assertEqual(self.api(ruta, 'DELETE', {'confirmar': True, 'version': 2}).status_code, 200)
        self.assertEqual(self.repo.listar('camiones', {'camion_id': 'CAM-222'}), [])

    def test_acceso_semaforo_y_busqueda(self):
        datos = dict(P=True, Q=False, R=True, S=True, H=True, T=False)
        r = self.api('/simular', 'POST', datos).json
        self.assertTrue(r['A']); self.assertTrue(r['E'])
        self.assertEqual(r['resultado'], 'inspeccion')
        self.assertFalse(self.api('/camion?placa=ABC-104-D').json['S'])
        r = self.api('/registros/accesos', 'POST', {**datos, 'camion_id': 'CAM-102', 'placa': 'ABC-102-D'})
        self.assertEqual(r.json['registro']['resultado'], 'inspeccion')
        self.assertEqual(self.api('/registros/accesos', 'POST', {}).status_code, 400)
        self.assertEqual(self.api('/simular', 'POST', {**datos, 'P': 'sí'}).status_code, 400)

    def test_correo_asincrono_edicion_y_notificacion_simulada(self):
        correo = dict(remitente='persona@ejemplo.test', asunto='Derrame', cuerpo='Fuga de químico del CAM-102 en andén 3.')
        r = self.terminar(self.api('/registros/incidentes', 'POST', correo))
        self.assertEqual(r['clasificacion']['prioridad'], 'critica')
        cambio = dict(id=r['_id'], version=1, categoria='otro', prioridad='baja', estado='cerrado',
                      resumen='Atendido por supervisor', requiere_revision_humana=False, motivo='Comprobación humana')
        self.assertEqual(self.api('/registros/incidentes', 'POST', cambio).json['registro']['estado'], 'cerrado')
        aviso = self.terminar(self.api('/notificar/' + r['_id'], 'POST', {'confirmar': True}))
        self.assertIn('no se envió', aviso['mensaje'])
        self.llm.chat.assert_not_called()

    def test_crud_riesgo_y_evaluacion(self):
        riesgo = dict(modulo='Web', descripcion='Error de supervisión', categoria='responsabilidad', probabilidad=3,
                      impacto=4, mitigacion='Revisión humana', probabilidad_residual=2, impacto_residual=3, evidencia='Ensayo local')
        evaluacion = dict(prompt='Pregunta', respuesta='Respuesta', modelo='manual', latencia_ms=12.5,
                          coincidio_reglas=None, observacion='Captura de revisión manual')
        for coleccion, datos in [('riesgos_eticos', riesgo), ('evaluaciones_llm', evaluacion)]:
            r = self.api('/registros/' + coleccion, 'POST', datos).json['registro']
            editado = self.api('/registros/' + coleccion, 'POST', {**datos, 'id': r['_id'], 'version': 1})
            self.assertEqual(editado.json['registro']['version'], 2)
            self.assertEqual(self.api('/registros/' + coleccion + '/' + r['_id'], 'DELETE', {'confirmar': True, 'version': 2}).status_code, 200)

    def test_asistente_usa_fuentes_y_no_inventa(self):
        r = self.terminar(self.api('/asistente', 'POST', {'pregunta': '¿Por qué CAM-102 fue a inspección?'}))
        self.assertTrue(r['fuentes'][0].startswith('accesos:'))
        self.assertIn('inspeccion', r['respuesta_mostrada'])
        vacio = self.terminar(self.api('/asistente', 'POST', {'pregunta': '¿Qué pasó con CAM-999?'}))
        self.assertIn('No tengo información', vacio['respuesta_mostrada'])
        self.assertEqual(len(self.api('/asistente/historial').json['registros']), 2)

    def test_exportaciones_descargables(self):
        for extension, comienzo in [('pdf', b'%PDF'), ('json', b'['), ('csv', b'\xef\xbb\xbf')]:
            r = self.api('/exportar/accesos/' + extension)
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.data.startswith(comienzo))
            self.assertIn('attachment', r.headers['Content-Disposition'])
        self.assertEqual(self.api('/registros/usuarios').status_code, 400)
        self.assertEqual(self.api('/exportar/accesos/py').status_code, 400)

    def test_revision_individual_sin_marcar_los_demas(self):
        corpus = self.api('/corpus').json
        datos = dict(id=corpus['registros'][0]['id'], revision=corpus['revision'],
                     categoria_esperada='otro', prioridad_esperada='baja', revisado_humano=True)
        r = self.api('/corpus/revisar', 'POST', datos).json
        self.assertEqual(r['revisados'], 1)
        self.assertEqual(r['registros'][0]['revisor'], self.servicio.config.operador)
        self.assertEqual(self.api('/corpus/revisar', 'POST', datos).status_code, 400)
        self.assertEqual(self.api('/corpus/exportar').status_code, 200)

    def test_experimento_real_solo_reglas(self):
        r = self.terminar(self.api('/experimento', 'POST', {'solo_reglas': True}))
        self.assertEqual(r['correos'], 30)
        self.assertIsNone(r['metricas']['llm']['exactitud_categoria'])
        self.assertEqual(r['etiquetas_revisadas_por_persona'], 0)
        self.assertAlmostEqual(r['metricas']['reglas']['exactitud_categoria'], 22/30)
        self.assertEqual(self.api('/experimento/exportar/json').status_code, 200)
        self.assertEqual(self.api('/experimento').json['resultado']['experimento'], r['experimento'])

    def test_configuracion_y_datos_demo(self):
        config = self.servicio.config.model_dump()
        r = self.api('/configuracion', 'POST', {**config, 'operador': 'Revisor web'})
        self.assertEqual(r.status_code, 200)
        self.guardar.assert_called_once()
        self.assertEqual(self.api('/configuracion', 'POST', {**config, 'url_ollama': 'https://nube.example'}).status_code, 400)
        resultado = self.terminar(self.api('/demostracion', 'POST', {'confirmar': True}))
        self.assertTrue(resultado['mensaje'].startswith('0 registros'))

    def test_operacion_lenta_no_bloquea_lecturas_y_rechaza_doble_escritura(self):
        listo = threading.Event()
        salir = threading.Event()
        self.addCleanup(salir.set)
        def esperar():
            listo.set()
            salir.wait(3)
            return 'Conexión de prueba'
        self.repo.comprobar = esperar
        primera = self.api('/conexion', 'POST', {})
        self.assertTrue(listo.wait(1))
        self.assertEqual(self.api('/panel').status_code, 200)
        self.assertEqual(self.api('/conexion', 'POST', {}).status_code, 409)
        self.assertEqual(self.api('/configuracion', 'POST', self.servicio.config.model_dump()).status_code, 409)
        salir.set()
        self.assertEqual(self.terminar(primera)['mensaje'], 'Conexión de prueba')


class TestWebTutor(ClienteWeb, unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.llm = Mock(modelo='sustituto_de_prueba')
        self.llm.chat.side_effect = [('SELECT titulo FROM libros;', 1), ('Consultamos títulos con SELECT.', 1)]
        self.tutor = TutorSQL(self.llm, Path(self.tmp.name) / 'historial.json')
        self.preparar(crear_tutor(self.tutor))

    def test_conversacion_resumen_exportacion_reinicio(self):
        self.assertIn('Tutor SQL', self.client.get('/').text)
        r = self.terminar(self.api('/preguntar', 'POST', {'pregunta': '¿Cómo consulto los títulos?'}))
        self.assertIn('SELECT', r['respuesta'])
        self.assertEqual(self.api('/estado').json['consultas'], 1)
        resumen = self.terminar(self.api('/resumen', 'POST', {}))
        self.assertIn('SELECT', resumen['resumen'])
        self.assertEqual(len(self.api('/exportar').json), 2)
        self.assertEqual(self.api('/historial', 'DELETE', {'confirmar': False}).status_code, 400)
        self.assertEqual(self.api('/historial', 'DELETE', {'confirmar': True}).status_code, 200)
        self.assertEqual(self.api('/estado').json['historial'], [])

    def test_error_de_modelo_sin_historial_ficticio(self):
        self.llm.chat.side_effect = ErrorLLM('No hay modelo local')
        response = self.api('/preguntar', 'POST', {'pregunta': 'Explica JOIN'})
        limite = time.monotonic() + 3
        while time.monotonic() < limite:
            r = self.api('/trabajos/' + response.json['trabajo']).json
            if r['estado'] == 'error': break
            time.sleep(.005)
        self.assertEqual(r['estado'], 'error')
        self.assertEqual(self.api('/estado').json['consultas'], 0)


if __name__ == '__main__':
    unittest.main()
