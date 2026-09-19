"""Validar reglas y persistencia con Atlas simulado; nunca leer credenciales reales."""

import contextlib
from datetime import timezone
import io
from pathlib import Path
from queue import Queue
import sys
import tempfile
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import quote_plus

from bson import ObjectId
from dotenv import dotenv_values
from pymongo.errors import ConnectionFailure, OperationFailure

DIRECTORIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DIRECTORIO))
from agente_climatizacion import AgenteClimatizacion
import almacenamiento_atlas as atlas
import configuracion
import interfaz
import preparar_env


def regla_original(temperatura, humedad):
    if temperatura > 30 and humedad > 70:
        return 'Encender aire acondicionado (Modo Deshumidificador)'
    if temperatura > 30:
        return 'Encender ventilador'
    if temperatura < 18:
        return 'Encender calefacción'
    return 'Mantener sistema apagado'


class ColeccionSimulada:
    def __init__(self):
        self.registros = []
        self.llamadas = 0
        self.fallo = None
        self.fallo_despues_de_insertar = False
        self.confirmar = True

    def insert_one(self, documento):
        self.llamadas += 1
        if self.fallo:
            raise self.fallo
        documento['_id'] = ObjectId()
        self.registros.append(dict(documento))
        if self.fallo_despues_de_insertar:
            raise ConnectionFailure('CREDENCIAL_PRIVADA_FICTICIA')
        return SimpleNamespace(acknowledged=self.confirmar, inserted_id=documento['_id'])

    def find_one(self, filtro, proyeccion, sort):
        assert filtro == {'practica': 10}
        assert proyeccion == atlas.PROYECCION
        assert sort == [('fecha', -1), ('_id', -1)]
        if self.fallo:
            raise self.fallo
        candidatos = [d for d in self.registros if d['practica'] == 10]
        return max(candidatos, key=lambda d: (d['fecha'], d['_id'])) if candidatos else None


class AgenteTest(unittest.TestCase):
    def test_reglas_del_profesor_y_valores_en_los_limites(self):
        agente = AgenteClimatizacion()
        temperaturas = [-40, 0, 17.999, 18, 18.001, 29.999, 30, 30.001, 31, 80]
        humedades = [0, 69.999, 70, 70.001, 100]
        for temperatura in temperaturas:
            for humedad in humedades:
                with self.subTest(temperatura=temperatura, humedad=humedad):
                    agente.percibir(temperatura, humedad)
                    self.assertEqual(agente.tomar_decision(), regla_original(temperatura, humedad))

    def test_decimales_y_resumen_en_espanol(self):
        agente = AgenteClimatizacion()
        agente.percibir(' 32,5 ', '70.5')
        self.assertEqual(agente.temperatura, 32.5)
        agente.tomar_decision()
        self.assertIn('32.5 °C', agente.mostrar_resultado())
        self.assertIn('Modo Deshumidificador', agente.mostrar_resultado())

    def test_datos_invalidos_no_permiten_ejecutar(self):
        agente = AgenteClimatizacion()
        almacenamiento = Mock()
        casos = [('', '40'), ('texto', '40'), ('NaN', '40'), ('inf', '40'),
                 ('-inf', '40'), ('1e999', '40'), ('20', 'NaN'), ('20', '-0.1'),
                 ('20', '100.1'), ('20', ''), ('1,2,3', '40'), (None, 40), (True, 40)]
        for temperatura, humedad in casos:
            with self.subTest(temperatura=temperatura, humedad=humedad):
                agente.percibir(20, 50)
                with self.assertRaises(ValueError):
                    agente.percibir(temperatura, humedad)
                with self.assertRaises(ValueError):
                    agente.ejecutar(almacenamiento)
        almacenamiento.insertar.assert_not_called()

    def test_no_inventa_una_lectura_inicial(self):
        agente = AgenteClimatizacion()
        with self.assertRaises(ValueError):
            agente.tomar_decision()
        with self.assertRaises(ValueError):
            agente.mostrar_resultado()


class AtlasTest(unittest.TestCase):
    def setUp(self):
        self.coleccion = ColeccionSimulada()
        self.almacenamiento = atlas.AlmacenamientoAtlas(self.coleccion)
        self.agente = AgenteClimatizacion()
        self.agente.percibir(35, 80)

    def test_el_agente_inserta_registros_nuevos_con_su_decision(self):
        primero = self.agente.ejecutar(self.almacenamiento)
        segundo = self.agente.ejecutar(self.almacenamiento)
        self.assertEqual(len(self.coleccion.registros), 2)
        self.assertNotEqual(primero['_id'], segundo['_id'])
        registro = self.coleccion.registros[0]
        self.assertEqual(registro['practica'], 10)
        self.assertEqual(registro['accion'], regla_original(35, 80))
        self.assertEqual(registro['alumno'], 'Einar Ivan Lazcano Luna')
        self.assertEqual(registro['temperatura'], 35.0)
        self.assertEqual(registro['humedad'], 80.0)
        self.assertEqual(registro['fecha'].tzinfo, timezone.utc)
        self.assertEqual(set(registro), set(atlas.CAMPOS) | {'_id'})

    def test_consulta_solo_la_practica10_sin_escribir(self):
        self.assertIsNone(self.almacenamiento.consultar_ultimo())
        primero = self.agente.ejecutar(self.almacenamiento)
        ajeno = {**self.coleccion.registros[0], 'practica': 9, '_id': ObjectId()}
        self.coleccion.registros.append(ajeno)
        self.assertEqual(self.almacenamiento.consultar_ultimo()['_id'], primero['_id'])
        self.assertEqual(self.coleccion.llamadas, 1)

    def test_error_tras_insertar_no_muestra_exito_ni_reintenta(self):
        self.coleccion.fallo_despues_de_insertar = True
        with self.assertRaises(atlas.ErrorAtlas) as resultado:
            self.agente.ejecutar(self.almacenamiento)
        self.assertIn('no se confirmó', str(resultado.exception))
        self.assertNotIn('CREDENCIAL', str(resultado.exception))
        self.assertEqual(self.coleccion.llamadas, 1)
        self.assertEqual(len(self.coleccion.registros), 1)
        self.assertIsNotNone(self.almacenamiento.consultar_ultimo())

    def test_permisos_y_confirmacion_de_escritura(self):
        self.coleccion.fallo = OperationFailure('CREDENCIAL_PRIVADA_FICTICIA', 13)
        with self.assertRaisesRegex(atlas.ErrorAtlas, 'permisos'):
            self.agente.ejecutar(self.almacenamiento)
        self.coleccion.fallo = None
        self.coleccion.confirmar = False
        with self.assertRaisesRegex(atlas.ErrorAtlas, 'no se confirmó'):
            self.agente.ejecutar(self.almacenamiento)

    def test_cliente_se_conecta_una_vez_y_se_cierra(self):
        cliente = Mock()
        cliente.__getitem__ = Mock(return_value={'climatizacion': self.coleccion})
        configuracion_falsa = ('mongodb://localhost.invalid/', 'base_de_prueba', 'climatizacion')
        almacenamiento = atlas.AlmacenamientoAtlas()
        with patch.object(atlas, 'cargar_configuracion', return_value=configuracion_falsa), patch.object(atlas, 'MongoClient', return_value=cliente) as fabrica:
            almacenamiento.consultar_ultimo()
            self.agente.ejecutar(almacenamiento)
            fabrica.assert_called_once()
        almacenamiento.cerrar()
        almacenamiento.cerrar()
        cliente.close.assert_called_once()

    def test_configuracion_invalida_no_abre_conexion(self):
        with patch.object(atlas, 'cargar_configuracion', side_effect=ValueError('Falta el archivo .env.')), patch.object(atlas, 'MongoClient') as cliente:
            with self.assertRaisesRegex(atlas.ErrorAtlas, 'Falta'):
                atlas.AlmacenamientoAtlas().consultar_ultimo()
            cliente.assert_not_called()


class ConfiguracionTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)
        self.destino = self.raiz / '.env'

    def test_reutilizar_configuracion9_sin_modificarla_ni_imprimirla(self):
        origen = self.raiz / 'origen.env'
        origen.write_text("Mongo_User='usuario_prueba'\nMongo_Password='ficticia@${NO_EXPANDIR}/'\nMongo_Closter='pruebas.mongodb.net'\nMongo_DB='base_anterior'\nMongo_Collection='datos'\n")
        anterior = origen.read_bytes()
        pedir = Mock(side_effect=AssertionError('No debe solicitar una contraseña disponible'))
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            self.assertTrue(preparar_env.crear_configuracion(self.destino, origen, pedir))
        self.assertEqual(origen.read_bytes(), anterior)
        valores = dotenv_values(self.destino, interpolate=False)
        self.assertEqual(valores['Mongo_Password'], 'ficticia@${NO_EXPANDIR}/')
        self.assertEqual(valores['Mongo_DB'], 'Einar_Ivan_Lazcano_Luna')
        self.assertEqual(valores['Mongo_Collection'], 'climatizacion')
        uri, base, coleccion = configuracion.cargar_configuracion(self.destino)
        self.assertIn(quote_plus(valores['Mongo_Password']), uri)
        self.assertIn('appName=Practica10', uri)
        self.assertNotIn('ficticia', salida.getvalue())
        self.assertEqual(self.destino.stat().st_mode & 0o777, 0o600)
        self.assertEqual(list(self.raiz.glob('.env-*')), [])

    def test_conservar_env_existente(self):
        preparar_env.crear_configuracion(self.destino, solicitar_clave=lambda _: 'clave_ficticia')
        anterior = self.destino.read_bytes()
        self.assertFalse(preparar_env.crear_configuracion(self.destino, solicitar_clave=Mock(side_effect=AssertionError)))
        self.assertEqual(self.destino.read_bytes(), anterior)

    def test_origen_invalido_no_deja_archivos(self):
        origen = self.raiz / 'origen.env'
        origen.write_text('Mongo_Password=\n')
        with self.assertRaises(ValueError):
            preparar_env.crear_configuracion(self.destino, origen)
        self.assertFalse(self.destino.exists())
        with self.assertRaises(ValueError):
            preparar_env.crear_configuracion(self.destino, solicitar_clave=lambda _: '')
        self.assertFalse(self.destino.exists())


class ControladorTest(unittest.TestCase):
    def crear_controlador(self, almacenamiento):
        app = interfaz.VentanaClimatizacion.__new__(interfaz.VentanaClimatizacion)
        app.ventana = Mock()
        app.almacenamiento = almacenamiento
        app.resultados = Queue()
        app.ocupado = app.cerrando = app.cerrada = False
        app.sondeo = None
        for nombre in ['temperatura','humedad','resumen','documento','vigencia','destino','estado','etiqueta_estado','progreso','entrada_temperatura','entrada_humedad']:
            setattr(app, nombre, Mock())
        app.temperatura.get.return_value = '35'
        app.humedad.get.return_value = '80'
        app.botones = (Mock(), Mock(), Mock())
        app.entradas = (app.entrada_temperatura, app.entrada_humedad)
        return app

    def test_muestra_decision_y_entrega_agente_a_la_insercion(self):
        app = self.crear_controlador(Mock())
        app._enviar = Mock()
        app.evaluar_y_guardar()
        self.assertIn('Modo Deshumidificador', app.resumen.set.call_args.args[0])
        operacion, agente = app._enviar.call_args.args
        self.assertEqual(operacion, 'guardar')
        self.assertIsInstance(agente, AgenteClimatizacion)
        self.assertEqual(agente.temperatura, 35)

    def test_validacion_y_limpiar_no_acceden_a_atlas(self):
        almacenamiento = Mock()
        app = self.crear_controlador(almacenamiento)
        app._enviar = Mock()
        app.humedad.get.return_value = '101'
        app.evaluar_y_guardar()
        app._enviar.assert_not_called()
        app.limpiar()
        app.temperatura.set.assert_called_with('')
        app.humedad.set.assert_called_with('')
        almacenamiento.insertar.assert_not_called()
        almacenamiento.consultar_ultimo.assert_not_called()

    def test_guardado_lento_no_bloquea_ni_se_duplica_y_espera_al_cerrar(self):
        iniciado, liberar = Event(), Event()
        self.addCleanup(liberar.set)
        almacenamiento = Mock(base='base_de_prueba', coleccion='climatizacion')
        def insertar(documento):
            iniciado.set()
            if not liberar.wait(5):
                raise RuntimeError('Trabajo no liberado por la prueba')
            return {'_id': 'id_simulado', 'accion': documento['accion']}
        almacenamiento.insertar.side_effect = insertar
        app = self.crear_controlador(almacenamiento)
        app.evaluar_y_guardar()
        self.assertTrue(iniciado.wait(2))
        self.assertTrue(app.ocupado)
        app.evaluar_y_guardar()
        self.assertEqual(almacenamiento.insertar.call_count, 1)
        app.cerrar()
        app.ventana.destroy.assert_not_called()
        liberar.set()
        resultado = app.resultados.get(timeout=2)
        app.resultados.put(resultado)
        app._recibir()
        app.ventana.destroy.assert_called_once()
        almacenamiento.cerrar.assert_called_once()

    def test_fallo_conserva_lecturas_y_no_presenta_guardado_exitoso(self):
        app = self.crear_controlador(Mock())
        app.ocupado = True
        app.resultados.put({'ok': False, 'mensaje': 'No se confirmó el guardado.', 'base': '', 'coleccion': '', 'operacion': 'guardar'})
        app._recibir()
        self.assertIn('No se confirmó', app.estado.set.call_args.args[0])
        app.temperatura.set.assert_not_called()
        app.humedad.set.assert_not_called()
        app.documento.delete.assert_not_called()
        self.assertFalse(app.ocupado)
        for control in (*app.botones, *app.entradas):
            control.state.assert_called_with(['!disabled'])


class VentanaRealTest(unittest.TestCase):
    def test_ventana_y_campos(self):
        try:
            ventana = interfaz.tk.Tk()
        except interfaz.tk.TclError:
            self.skipTest('Se necesita un escritorio o WSLg para esta prueba visual.')
        self.addCleanup(ventana.destroy)
        app = interfaz.VentanaClimatizacion(ventana, atlas.AlmacenamientoAtlas(ColeccionSimulada()))
        ventana.update_idletasks()
        app.temperatura.set('32,5')
        app.humedad.set('80')
        app._enviar = Mock()
        app.evaluar_y_guardar()
        self.assertIn('Modo Deshumidificador', app.resumen.get())
        self.assertGreater(app.entrada_temperatura.winfo_width(), 100)
        app.limpiar()
        self.assertEqual(app.temperatura.get(), '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
