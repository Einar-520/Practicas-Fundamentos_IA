"""Pruebas con Atlas simulado; no usan el .env ni una conexión de red."""

import importlib.util
from pathlib import Path
from queue import Queue
import sys
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pymongo.errors import ConnectionFailure, OperationFailure

DIRECTORIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DIRECTORIO))
import servicio_atlas as atlas
import interfaz_tkinter as interfaz

spec = importlib.util.spec_from_file_location('web_atlas', DIRECTORIO / '09_conexion_mongodb_atlas.py')
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)


class ColeccionSimulada:
    def __init__(self):
        self.documento = None
        self.escrituras = 0
        self.error_lectura = False
        self.error_escritura = False

    def find_one(self, filtro, proyeccion):
        assert filtro == {'_id': 'practica_09'}
        assert proyeccion == atlas.PROYECCION
        if self.error_lectura:
            raise ConnectionFailure('URI_PRIVADA_FICTICIA')
        return self.documento

    def update_one(self, filtro, cambio, upsert):
        assert filtro == {'_id': 'practica_09'} and upsert
        if self.error_escritura:
            raise OperationFailure('URI_PRIVADA_FICTICIA', 13)
        nuevo = self.documento is None
        self.documento = {**(self.documento or {}), **filtro, **cambio['$set']}
        self.escrituras += 1
        return SimpleNamespace(upserted_id='practica_09' if nuevo else None)


class ServicioTest(unittest.TestCase):
    def setUp(self):
        self.coleccion = ColeccionSimulada()
        self.servicio = atlas.ServicioAtlas(self.coleccion)

    def test_consultar_no_escribe_y_guardar_actualiza_el_mismo_documento(self):
        self.assertIsNone(self.servicio.consultar())
        self.assertEqual(self.coleccion.escrituras, 0)
        resultado = self.servicio.guardar('  Mi primer dato 🌱  ')
        self.assertEqual(resultado['documento']['dato'], 'Mi primer dato 🌱')
        self.assertEqual(resultado['documento']['id'], 'practica_09')
        self.coleccion.documento['campo_ajeno'] = 'conservar'
        segundo = self.servicio.guardar('Dato actualizado')
        self.assertEqual(segundo['documento']['id'], resultado['documento']['id'])
        self.assertEqual(self.coleccion.documento['campo_ajeno'], 'conservar')
        self.assertNotIn('campo_ajeno', segundo['documento'])
        self.assertEqual(segundo['documento']['nombre'], 'Einar Ivan Lazcano Luna')

    def test_validacion_antes_de_conectar(self):
        for dato in ['', ' \n\t', 'x' * 1001, None, 23]:
            with self.subTest(dato=str(dato)[:20]), patch.object(atlas, 'MongoClient') as cliente:
                with self.assertRaises(atlas.ErrorAtlas) as fallo:
                    atlas.ServicioAtlas().guardar(dato)
                self.assertEqual(fallo.exception.codigo, 400)
                cliente.assert_not_called()
        self.assertEqual(len(self.servicio.guardar('🌱' * 1000)['documento']['dato']), 1000)

    def test_guardado_confirmado_con_lectura_fallida(self):
        self.coleccion.error_lectura = True
        with self.assertRaises(atlas.ErrorAtlas) as fallo:
            self.servicio.guardar('Dato persistido')
        self.assertTrue(fallo.exception.guardado)
        self.assertEqual(self.coleccion.documento['dato'], 'Dato persistido')
        self.assertNotIn('URI_PRIVADA', str(fallo.exception))

    def test_error_de_escritura_no_se_confunde_con_exito(self):
        self.coleccion.error_escritura = True
        with self.assertRaises(atlas.ErrorAtlas) as fallo:
            self.servicio.guardar('No guardado')
        self.assertFalse(fallo.exception.guardado)
        self.assertEqual(self.coleccion.escrituras, 0)
        self.assertNotIn('URI_PRIVADA', str(fallo.exception))

    def test_configuracion_corregida_permite_reintentar_y_cerrar_cliente(self):
        cliente = Mock()
        cliente.__getitem__ = Mock(return_value={'datos': self.coleccion})
        servicio = atlas.ServicioAtlas()
        with patch.object(atlas, 'cargar_configuracion', side_effect=ValueError('Falta el archivo .env.')):
            with self.assertRaisesRegex(atlas.ErrorAtlas, 'Falta'):
                servicio.consultar()
        configuracion = ('mongodb://localhost.invalid/', 'base_de_prueba', 'datos')
        with patch.object(atlas, 'cargar_configuracion', return_value=configuracion), patch.object(atlas, 'MongoClient', return_value=cliente):
            self.assertIsNone(servicio.consultar())
        servicio.cerrar()
        servicio.cerrar()
        cliente.close.assert_called_once()


class WebTest(unittest.TestCase):
    def setUp(self):
        self.coleccion = ColeccionSimulada()
        self.cliente = web.crear_app(self.coleccion).test_client()
        self.assertEqual(self.cliente.get('/').status_code, 200)
        with self.cliente.session_transaction() as sesion:
            self.token = sesion['csrf']

    def test_api_conserva_contrato_csrf_y_dato(self):
        self.assertEqual(self.cliente.get('/api/documento').json, {'ok': True, 'documento': None})
        for token in ['', 'incorrecto', 'ñ']:
            respuesta = self.cliente.post('/api/documento', data={'csrf': token, 'dato': 'Prueba'})
            self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(self.coleccion.escrituras, 0)
        respuesta = self.cliente.post('/api/documento', data={'csrf': self.token, 'dato': 'Prueba'})
        self.assertTrue(respuesta.json['ok'])
        self.assertEqual(respuesta.json['documento']['dato'], 'Prueba')
        self.assertEqual(self.cliente.post('/api/documento', data={'csrf': self.token, 'dato': ' '}).status_code, 400)
        self.assertEqual(self.cliente.post('/api/documento', data={'csrf': self.token, 'dato': 'x'*20000}).status_code, 413)

    def test_error_confirmado_y_archivos_privados(self):
        self.coleccion.error_lectura = True
        resultado = self.cliente.post('/api/documento', data={'csrf': self.token, 'dato': 'Prueba'})
        self.assertEqual(resultado.status_code, 503)
        self.assertTrue(resultado.json['guardado'])
        for ruta in ['/.env', '/servicio_atlas.py', '/configuracion.py']:
            self.assertEqual(self.cliente.get(ruta).status_code, 404)
        for ruta in ['/static/app.js', '/static/estilos.css']:
            with self.cliente.get(ruta) as respuesta:
                self.assertEqual(respuesta.status_code, 200)


class ControladorTest(unittest.TestCase):
    def crear_controlador(self, servicio):
        # Dobles de widgets para verificar el flujo aun sin un servidor gráfico.
        app = interfaz.VentanaAtlas.__new__(interfaz.VentanaAtlas)
        app.ventana = Mock()
        app.servicio = servicio
        app.resultados = Queue()
        app.ocupado = app.cerrando = app.cerrada = False
        app.sondeo = None
        for nombre in ['entrada', 'documento', 'contador', 'estado', 'destino', 'vigencia', 'etiqueta_estado', 'progreso']:
            setattr(app, nombre, Mock())
        app.botones = (Mock(), Mock(), Mock())
        return app

    def test_trabajo_lento_no_bloquea_ni_duplica_operaciones_y_cierra_al_terminar(self):
        iniciado, liberar = Event(), Event()
        self.addCleanup(liberar.set)
        servicio = Mock(base='base_de_prueba', coleccion='datos')
        def consultar():
            iniciado.set()
            if not liberar.wait(5):
                raise RuntimeError('La prueba no liberó el trabajo')
            return None
        servicio.consultar.side_effect = consultar
        app = self.crear_controlador(servicio)
        app.actualizar()
        self.assertTrue(iniciado.wait(2))
        self.assertTrue(app.ocupado)
        app.actualizar()
        self.assertEqual(servicio.consultar.call_count, 1)
        app.cerrar()
        app.ventana.destroy.assert_not_called()
        liberar.set()
        respuesta = app.resultados.get(timeout=2)
        app.resultados.put(respuesta)
        app._recibir()
        self.assertTrue(app.cerrada)
        servicio.cerrar.assert_called_once()
        app.ventana.destroy.assert_called_once()

    def test_limpiar_y_validar_no_escriben_en_atlas(self):
        servicio = Mock()
        app = self.crear_controlador(servicio)
        app.limpiar()
        app.entrada.delete.assert_called_once_with('1.0', 'end')
        for valor in [' ', 'x'*1001]:
            app.entrada.get.return_value = valor
            app.guardar()
        servicio.guardar.assert_not_called()
        servicio.consultar.assert_not_called()

    def test_error_de_red_conserva_formulario_y_marca_resultado_anterior(self):
        app = self.crear_controlador(Mock())
        app.ocupado = True
        app.resultados.put({'ok': False, 'mensaje': 'No hay conexión.', 'base': '', 'coleccion': ''})
        app._recibir()
        app.entrada.delete.assert_not_called()
        app.documento.delete.assert_not_called()
        self.assertIn('desactualizada', app.vigencia.set.call_args.args[0])
        self.assertFalse(app.ocupado)
        for boton in app.botones:
            boton.state.assert_called_with(['!disabled'])

    def test_trabajo_de_fondo_oculta_excepciones_no_controladas(self):
        servicio = Mock(base='', coleccion='')
        servicio.guardar.side_effect = RuntimeError('URI_PRIVADA_FICTICIA')
        resultados = Queue()
        interfaz.ejecutar_operacion(servicio, 'guardar', 'dato', resultados)
        mensaje = resultados.get_nowait()
        self.assertFalse(mensaje['ok'])
        self.assertNotIn('URI_PRIVADA', mensaje['mensaje'])


class VentanaRealTest(unittest.TestCase):
    def test_creacion_y_limpiar_con_tk_real(self):
        try:
            ventana = interfaz.tk.Tk()
        except interfaz.tk.TclError:
            self.skipTest('No hay servidor gráfico; ejecutar esta prueba en WSLg o escritorio.')
        self.addCleanup(lambda: ventana.destroy() if ventana.winfo_exists() else None)
        with patch.object(interfaz.VentanaAtlas, 'actualizar'):
            app = interfaz.VentanaAtlas(ventana, atlas.ServicioAtlas(ColeccionSimulada()))
        ventana.update_idletasks()
        app.entrada.insert('1.0', 'Un dato')
        ventana.update()
        self.assertIn('7 / 1000', app.contador.get())
        app.limpiar()
        self.assertEqual(app.entrada.get('1.0', 'end-1c'), '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
