"""Validar reglas y persistencia con Atlas simulado; nunca leer credenciales reales."""

import contextlib
from copy import deepcopy
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


class CursorSimulado(list):
    def sort(self, orden):
        resultado = list(self)
        for campo, direccion in reversed(orden):
            resultado.sort(key=lambda d: d[campo], reverse=direccion < 0)
        return CursorSimulado(resultado)

    def skip(self, cantidad):
        return CursorSimulado(self[cantidad:])

    def limit(self, cantidad):
        return CursorSimulado(self[:cantidad])


class ColeccionSimulada:
    def __init__(self):
        self.registros = []
        self.llamadas = 0
        self.fallo = None
        self.fallo_lectura = False
        self.fallo_despues_de_insertar = False
        self.confirmar = True
        self.modificados_cero = False

    @staticmethod
    def coincide(documento, filtro):
        return all(documento.get(k) == v for k, v in filtro.items())

    def insert_one(self, documento):
        self.llamadas += 1
        if self.fallo:
            raise self.fallo
        documento['_id'] = ObjectId()
        self.registros.append(deepcopy(documento))
        if self.fallo_despues_de_insertar:
            raise ConnectionFailure('CREDENCIAL_PRIVADA_FICTICIA')
        return SimpleNamespace(acknowledged=self.confirmar, inserted_id=documento['_id'])

    def find(self, filtro, proyeccion):
        assert filtro == atlas.FILTRO_BASE
        assert proyeccion == atlas.PROYECCION
        if self.fallo:
            raise self.fallo
        if self.fallo_lectura:
            raise ConnectionFailure('CREDENCIAL_PRIVADA_FICTICIA')
        return CursorSimulado(deepcopy(d) for d in self.registros if self.coincide(d, filtro))

    def find_one(self, filtro, proyeccion, sort):
        documentos = self.find(filtro, proyeccion).sort(sort)
        return documentos[0] if documentos else None

    def update_one(self, filtro, cambio, upsert):
        assert upsert is False
        assert set(filtro) == {'_id', 'practica', 'alumno'}
        assert filtro['practica'] == 10 and filtro['alumno'] == atlas.ALUMNO
        if self.fallo:
            raise self.fallo
        for documento in self.registros:
            if self.coincide(documento, filtro):
                documento.update(deepcopy(cambio['$set']))
                return SimpleNamespace(acknowledged=self.confirmar, matched_count=1,
                                       modified_count=0 if self.modificados_cero else 1)
        return SimpleNamespace(acknowledged=self.confirmar, matched_count=0, modified_count=0)

    def delete_one(self, filtro):
        assert set(filtro) == {'_id', 'practica', 'alumno'}
        assert filtro['practica'] == 10 and filtro['alumno'] == atlas.ALUMNO
        if self.fallo:
            raise self.fallo
        for indice, documento in enumerate(self.registros):
            if self.coincide(documento, filtro):
                del self.registros[indice]
                return SimpleNamespace(acknowledged=self.confirmar, deleted_count=1)
        return SimpleNamespace(acknowledged=self.confirmar, deleted_count=0)


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


class CrudTest(unittest.TestCase):
    def setUp(self):
        self.coleccion = ColeccionSimulada()
        self.almacenamiento = atlas.AlmacenamientoAtlas(self.coleccion)
        self.agente = AgenteClimatizacion()
        self.agente.percibir(35, 80)
        self.creado = self.agente.ejecutar(self.almacenamiento)

    def test_crud_completo_recalcula_y_conserva_fecha_y_campos_ajenos(self):
        fecha = self.coleccion.registros[0]['fecha']
        self.coleccion.registros[0]['nota_del_profesor'] = 'Conservar'
        self.agente.percibir(16, 50)
        actualizado = self.agente.ejecutar(self.almacenamiento, self.creado['_id'])
        self.assertEqual(actualizado['_id'], self.creado['_id'])
        listado = self.almacenamiento.listar()
        self.assertEqual(len(listado['registros']), 1)
        self.assertEqual(listado['registros'][0]['accion'], 'Encender calefacción')
        self.assertIn('actualizado_en', listado['registros'][0])
        self.assertEqual(self.coleccion.registros[0]['fecha'], fecha)
        self.assertEqual(self.coleccion.registros[0]['nota_del_profesor'], 'Conservar')
        self.assertNotIn('nota_del_profesor', listado['registros'][0])
        self.almacenamiento.eliminar(self.creado['_id'])
        self.assertEqual(self.almacenamiento.listar()['registros'], [])

    def test_no_consulta_edita_ni_borra_otras_practicas_o_alumnos(self):
        registro = self.coleccion.registros[0]
        ajenos = [{**registro, '_id': ObjectId(), 'practica': 9},
                  {**registro, '_id': ObjectId(), 'alumno': 'Otro alumno'}]
        self.coleccion.registros.extend(deepcopy(ajenos))
        self.assertEqual(len(self.almacenamiento.listar()['registros']), 1)
        for ajeno in ajenos:
            with self.assertRaises(atlas.ErrorAtlas):
                self.agente.ejecutar(self.almacenamiento, str(ajeno['_id']))
            with self.assertRaises(atlas.ErrorAtlas):
                self.almacenamiento.eliminar(str(ajeno['_id']))
        self.almacenamiento.eliminar(self.creado['_id'])
        self.assertEqual(self.coleccion.registros, ajenos)

    def test_ids_invalidos_se_rechazan_antes_de_conectar(self):
        almacenamiento = atlas.AlmacenamientoAtlas()
        for identificador in ['', 'no-es-un-id', None, {'$ne': None}]:
            with self.subTest(identificador=identificador), patch.object(almacenamiento, 'abrir') as abrir:
                with self.assertRaises(ValueError):
                    almacenamiento.actualizar(identificador, {})
                with self.assertRaises(ValueError):
                    almacenamiento.eliminar(identificador)
                abrir.assert_not_called()

    def test_inexistente_no_crea_un_registro_al_editar(self):
        for operacion in [lambda: self.agente.ejecutar(self.almacenamiento, str(ObjectId())),
                          lambda: self.almacenamiento.eliminar(str(ObjectId()))]:
            with self.assertRaisesRegex(atlas.ErrorAtlas, 'ya no existe'):
                operacion()
        self.assertEqual(len(self.coleccion.registros), 1)
        self.assertEqual(self.coleccion.llamadas, 1)

    def test_matched_count_permita_guardado_sin_cambios_y_ack_es_obligatorio(self):
        self.coleccion.modificados_cero = True
        self.agente.ejecutar(self.almacenamiento, self.creado['_id'])
        self.coleccion.confirmar = False
        with self.assertRaisesRegex(atlas.ErrorAtlas, 'no se confirmó'):
            self.agente.ejecutar(self.almacenamiento, self.creado['_id'])
        with self.assertRaisesRegex(atlas.ErrorAtlas, 'no se confirmó'):
            self.almacenamiento.eliminar(self.creado['_id'])

    def test_paginacion_permite_recuperar_todos_los_registros(self):
        for _ in range(atlas.TAMANO_PAGINA + 2):
            self.agente.ejecutar(self.almacenamiento)
        primera, segunda = self.almacenamiento.listar(0), self.almacenamiento.listar(1)
        self.assertEqual(len(primera['registros']), atlas.TAMANO_PAGINA)
        self.assertTrue(primera['hay_siguiente'])
        self.assertEqual(len(segunda['registros']), 3)
        self.assertFalse(segunda['hay_siguiente'])
        ids = [d['_id'] for d in primera['registros'] + segunda['registros']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), len(self.coleccion.registros))
        for pagina in [-1, '1', True]:
            with self.assertRaises(ValueError):
                self.almacenamiento.listar(pagina)

    def test_errores_de_edicion_y_eliminacion_no_exponen_detalles(self):
        self.coleccion.fallo = ConnectionFailure('CREDENCIAL_PRIVADA_FICTICIA')
        for operacion in [lambda: self.agente.ejecutar(self.almacenamiento, self.creado['_id']),
                          lambda: self.almacenamiento.eliminar(self.creado['_id'])]:
            with self.assertRaises(atlas.ErrorAtlas) as error:
                operacion()
            self.assertNotIn('CREDENCIAL', str(error.exception))
        self.assertEqual(len(self.coleccion.registros), 1)

    def test_crear_editar_y_borrar_confirmados_con_refresco_fallido(self):
        self.coleccion.fallo_lectura = True
        for operacion in ['crear', 'actualizar', 'eliminar']:
            resultados = Queue()
            interfaz.trabajar(self.almacenamiento, operacion, self.agente, resultados,
                              identificador=self.creado['_id'])
            respuesta = resultados.get_nowait()
            self.assertFalse(respuesta['ok'])
            self.assertTrue(respuesta['confirmado'])
            self.assertIn('confirmado', respuesta['mensaje'])
            self.assertIn('Actualizar lista', respuesta['mensaje'])
            self.assertNotIn('CREDENCIAL', respuesta['mensaje'])
        self.assertEqual(len(self.coleccion.registros), 1)


class ControladorTest(unittest.TestCase):
    def crear_controlador(self, almacenamiento):
        app = interfaz.VentanaClimatizacion.__new__(interfaz.VentanaClimatizacion)
        app.ventana = Mock()
        app.almacenamiento = almacenamiento
        app.resultados = Queue()
        app.ocupado = app.cerrando = app.cerrada = app.renderizando = False
        app.sondeo = None
        app.registros = {}
        app.seleccionado = app.pendiente_seleccion = None
        app.pagina = 0
        app.hay_siguiente = False
        app.lista_vigente = True
        for nombre in ['temperatura','humedad','resumen','documento','vigencia','destino','estado',
                       'etiqueta_estado','progreso','entrada_temperatura','entrada_humedad',
                       'modo','tabla','paginacion','boton_guardar','boton_actualizar','boton_eliminar',
                       'boton_limpiar','boton_consultar','boton_anterior','boton_siguiente']:
            setattr(app, nombre, Mock())
        app.tabla.selection.return_value = ()
        app.tabla.get_children.return_value = ()
        app.temperatura.get.return_value = '35'
        app.humedad.get.return_value = '80'
        app.botones = (app.boton_guardar, app.boton_actualizar, app.boton_eliminar,
                       app.boton_limpiar, app.boton_consultar)
        app.entradas = (app.entrada_temperatura, app.entrada_humedad)
        return app

    def seleccionar(self, app):
        identificador = str(ObjectId())
        app.registros = {identificador: {'_id': identificador, 'temperatura': 35,
                                       'humedad': 80, 'accion': regla_original(35,80)}}
        app.tabla.selection.return_value = (identificador,)
        app.seleccionar_registro()
        return identificador

    def test_crear_y_editar_utilizan_el_agente_y_la_seleccion_correcta(self):
        app = self.crear_controlador(Mock())
        app._enviar = Mock()
        app.evaluar_y_guardar()
        self.assertIn('Modo Deshumidificador', app.resumen.set.call_args.args[0])
        self.assertEqual(app._enviar.call_args.args[0], 'crear')
        identificador = self.seleccionar(app)
        app.temperatura.get.return_value = '16'
        app.guardar_cambios()
        operacion, agente, seleccionado = app._enviar.call_args.args
        self.assertEqual((operacion,seleccionado), ('actualizar',identificador))
        self.assertEqual(agente.accion, 'Encender calefacción')
        app._enviar.reset_mock()
        app.evaluar_y_guardar()
        app._enviar.assert_not_called()

    def test_cancelar_eliminacion_no_escribe_y_confirmar_borra_solo_seleccionado(self):
        app = self.crear_controlador(Mock())
        app._enviar = Mock()
        identificador = self.seleccionar(app)
        with patch.object(interfaz.messagebox, 'askyesno', return_value=False) as preguntar:
            app.eliminar_seleccionado()
            self.assertIn(identificador, preguntar.call_args.args[1])
            self.assertEqual(preguntar.call_args.kwargs['default'], 'no')
        app._enviar.assert_not_called()
        with patch.object(interfaz.messagebox, 'askyesno', return_value=True):
            app.eliminar_seleccionado()
        app._enviar.assert_called_once_with('eliminar', identificador=identificador)

    def test_validacion_limpiar_y_falta_de_seleccion_no_escriben(self):
        app = self.crear_controlador(Mock())
        app._enviar = Mock()
        app.humedad.get.return_value = '101'
        app.evaluar_y_guardar()
        app.guardar_cambios()
        with patch.object(interfaz.messagebox, 'askyesno') as preguntar:
            app.eliminar_seleccionado()
            preguntar.assert_not_called()
        app._enviar.assert_not_called()
        app.limpiar()
        app.temperatura.set.assert_called_with('')
        app.humedad.set.assert_called_with('')
        self.assertIsNone(app.seleccionado)

    def test_trabajo_lento_no_duplica_y_espera_al_cerrar(self):
        iniciado, liberar = Event(), Event()
        self.addCleanup(liberar.set)
        almacenamiento = Mock(base='base_de_prueba', coleccion='climatizacion')
        def insertar(documento):
            iniciado.set()
            if not liberar.wait(5):
                raise RuntimeError('Trabajo no liberado por la prueba')
            return {'_id': str(ObjectId()), **documento}
        almacenamiento.insertar.side_effect = insertar
        almacenamiento.listar.return_value = {'registros': [], 'pagina': 0, 'hay_siguiente': False}
        app = self.crear_controlador(almacenamiento)
        app.evaluar_y_guardar()
        self.assertTrue(iniciado.wait(2))
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

    def test_fallo_conserva_campos_y_bloquea_escrituras_hasta_refrescar(self):
        app = self.crear_controlador(Mock())
        app.ocupado = True
        app.resultados.put({'ok': False, 'confirmado': False, 'mensaje': 'No se confirmó el guardado.',
                           'base': '', 'coleccion': '', 'operacion': 'crear'})
        app._recibir()
        self.assertIn('No se confirmó', app.estado.set.call_args.args[0])
        app.temperatura.set.assert_not_called()
        app.humedad.set.assert_not_called()
        app.documento.delete.assert_not_called()
        self.assertFalse(app.lista_vigente)
        app.boton_guardar.state.assert_called_with(['disabled'])
        app.boton_actualizar.state.assert_called_with(['disabled'])
        app.boton_eliminar.state.assert_called_with(['disabled'])
        app.boton_consultar.state.assert_called_with(['!disabled'])

    def test_refrescar_preserva_edicion_sin_cambiar_su_destinatario(self):
        app = self.crear_controlador(Mock())
        identificador = self.seleccionar(app)
        registro = app.registros[identificador]
        app.temperatura.set.reset_mock()
        app.humedad.set.reset_mock()
        app.ocupado = True
        app.resultados.put({'ok': True, 'confirmado': False, 'mensaje': 'Consulta completada.',
                           'base': '', 'coleccion': '', 'operacion': 'listar',
                           'listado': {'registros': [registro], 'pagina': 0, 'hay_siguiente': False}})
        app._recibir()
        app.seleccionar_registro()
        self.assertEqual(app.seleccionado, identificador)
        app.temperatura.set.assert_not_called()
        app.humedad.set.assert_not_called()

    def test_creacion_confirmada_vuelve_a_primera_pagina_tras_fallo_de_consulta(self):
        app = self.crear_controlador(Mock())
        app.pagina = 3
        identificador = str(ObjectId())
        app.resultados.put({'ok': False, 'confirmado': True, 'identificador': identificador,
                           'mensaje': 'Creación confirmada. Actualiza la lista.', 'operacion': 'crear',
                           'base': '', 'coleccion': ''})
        app._recibir()
        self.assertEqual(app.pagina, 0)
        self.assertEqual(app.pendiente_seleccion, identificador)
        app._enviar = Mock()
        app.consultar()
        app._enviar.assert_called_with('listar', pagina=0)

    def test_flujo_gui_crud_con_atlas_simulado(self):
        almacenamiento = atlas.AlmacenamientoAtlas(ColeccionSimulada())
        app = self.crear_controlador(almacenamiento)
        def recibir():
            respuesta = app.resultados.get(timeout=2)
            app.resultados.put(respuesta)
            app._recibir()
        app.evaluar_y_guardar()
        recibir()
        identificador = app.seleccionado
        self.assertIn(identificador, app.registros)
        app.temperatura.get.return_value = '16'
        app.guardar_cambios()
        recibir()
        self.assertEqual(app.registros[identificador]['accion'], 'Encender calefacción')
        with patch.object(interfaz.messagebox, 'askyesno', return_value=True):
            app.eliminar_seleccionado()
        recibir()
        self.assertEqual(app.registros, {})
        self.assertIsNone(app.seleccionado)


class VentanaRealTest(unittest.TestCase):
    def test_ventana_y_campos(self):
        try:
            ventana = interfaz.tk.Tk()
        except interfaz.tk.TclError:
            self.skipTest('Se necesita un escritorio o WSLg para esta prueba visual.')
        self.addCleanup(ventana.destroy)
        with patch.object(interfaz.VentanaClimatizacion, 'consultar'):
            app = interfaz.VentanaClimatizacion(ventana, atlas.AlmacenamientoAtlas(ColeccionSimulada()))
        app.lista_vigente = True
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
