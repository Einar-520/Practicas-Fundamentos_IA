"""Verificar controles Tkinter y gráficas sin escribir en el clúster real."""

from datetime import datetime, timezone
from pathlib import Path
from queue import Queue
import sys
from threading import Event
import unittest
from unittest.mock import Mock, patch

from bson import ObjectId
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

DIRECTORIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DIRECTORIO))
import almacenamiento_atlas as atlas
import interfaz
from agente_climatizacion import ACCIONES, AgenteClimatizacion
from graficas import dibujar_graficas, preparar_serie
from test_practica10 import ColeccionSimulada, regla_original


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
        app.filtro_accion = Mock()
        app.filtro_accion.get.return_value = interfaz.TODAS
        app.selector_accion = Mock()
        app.regla = Mock()
        app._actualizar_graficas = Mock()
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
        app.documento.delete.assert_called()
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



class FiltroYGraficasTest(unittest.TestCase):
    crear_controlador = ControladorTest.crear_controlador
    seleccionar = ControladorTest.seleccionar
    def test_cambio_de_accion_limpia_tabla_y_graficas_y_reinicia_pagina(self):
        app = self.crear_controlador(Mock())
        app.pagina = 3
        self.seleccionar(app)
        app.filtro_accion.get.return_value = ACCIONES[1]
        app._enviar = Mock()
        app.cambiar_accion()
        self.assertEqual(app.pagina, 0)
        self.assertIsNone(app.seleccionado)
        self.assertFalse(app.lista_vigente)
        self.assertEqual(app.registros, {})
        self.assertEqual(app._actualizar_graficas.call_args.args[0], [])
        app._enviar.assert_called_once_with('listar', pagina=0)

    def test_worker_filtra_las_cuatro_acciones_y_no_inserta_al_consultar(self):
        coleccion = ColeccionSimulada()
        almacenamiento = atlas.AlmacenamientoAtlas(coleccion)
        agente = AgenteClimatizacion()
        for temperatura, humedad in [(35, 80), (32, 60), (16, 30), (25, 50)]:
            agente.percibir(temperatura, humedad)
            agente.ejecutar(almacenamiento)
        for accion in ACCIONES:
            resultados = Queue()
            interfaz.trabajar(almacenamiento, 'listar', None, resultados, accion=accion)
            respuesta = resultados.get_nowait()
            self.assertTrue(respuesta['ok'])
            self.assertEqual([r['accion'] for r in respuesta['listado']['registros']], [accion])
            app = self.crear_controlador(almacenamiento)
            app._aplicar_listado(respuesta)
            representados = app._actualizar_graficas.call_args.args[0]
            self.assertEqual(representados, respuesta['listado']['registros'])
        self.assertEqual(coleccion.llamadas, 4)

    def test_edicion_fuera_del_filtro_informa_y_limpia_seleccion(self):
        coleccion = ColeccionSimulada()
        almacenamiento = atlas.AlmacenamientoAtlas(coleccion)
        agente = AgenteClimatizacion()
        agente.percibir(32, 60)
        creado = agente.ejecutar(almacenamiento)
        agente.percibir(25, 60)
        resultados = Queue()
        interfaz.trabajar(almacenamiento, 'actualizar', agente, resultados,
                          identificador=creado['_id'], accion=ACCIONES[1])
        respuesta = resultados.get_nowait()
        self.assertTrue(respuesta['confirmado'])
        self.assertIn('Para verlo selecciona', respuesta['mensaje'])
        self.assertEqual(respuesta['listado']['registros'], [])
        app = self.crear_controlador(almacenamiento)
        app.seleccionado = creado['_id']
        app.resultados.put(respuesta)
        app._recibir()
        self.assertIsNone(app.seleccionado)
        self.assertEqual(app.registros, {})

    def test_crear_editar_borrar_confirmados_con_consulta_fallida(self):
        coleccion = ColeccionSimulada()
        almacenamiento = atlas.AlmacenamientoAtlas(coleccion)
        agente = AgenteClimatizacion()
        agente.percibir(32, 60)
        creado = agente.ejecutar(almacenamiento)
        coleccion.fallo_lectura = True
        for operacion in ('crear','actualizar','eliminar'):
            resultados = Queue()
            interfaz.trabajar(almacenamiento, operacion, agente, resultados,
                              identificador=creado['_id'], accion=ACCIONES[1])
            respuesta = resultados.get_nowait()
            self.assertTrue(respuesta['confirmado'])
            self.assertFalse(respuesta['ok'])
            self.assertIn('confirmado', respuesta['mensaje'])
            self.assertIn('Actualizar lista', respuesta['mensaje'])
        self.assertEqual(coleccion.llamadas, 2)


class MatplotlibTest(unittest.TestCase):
    def test_fechas_utc_orden_valores_y_dibujo_de_la_pagina(self):
        registros = [
            {'_id':'b','fecha':'2026-10-02T17:30:00+00:00','temperatura':34,'humedad':60},
            {'_id':'a','fecha':'2026-10-02T10:00:00-06:00','temperatura':31,'humedad':50},
        ]
        serie = preparar_serie(registros, 'temperatura')
        self.assertEqual([p[1] for p in serie], ['a','b'])
        self.assertEqual(serie[0][0].hour, 16)
        figura = Figure(figsize=(8,3), layout='constrained')
        texto = dibujar_graficas(figura, registros)
        FigureCanvasAgg(figura).draw()
        self.assertEqual(list(figura.axes[0].lines[0].get_ydata()), [31,34])
        self.assertEqual(list(figura.axes[1].lines[0].get_ydata()), [50,60])
        self.assertEqual(figura.axes[1].get_ylim(), (0,100))
        self.assertIn('2 registros', texto)

    def test_un_punto_vacios_y_errores_no_dejan_la_grafica_anterior(self):
        figura = Figure(figsize=(8,3), layout='constrained')
        datos = [{'_id':'a','fecha':datetime.now(timezone.utc),'temperatura':32,'humedad':60}]
        dibujar_graficas(figura, datos)
        FigureCanvasAgg(figura).draw()
        self.assertEqual(figura.axes[0].lines[0].get_marker(), 'o')
        dibujar_graficas(figura, [], 'Consulta pendiente')
        FigureCanvasAgg(figura).draw()
        for eje in figura.axes:
            self.assertEqual(len(eje.lines), 0)
            self.assertEqual(eje.texts[0].get_text(), 'Consulta pendiente')

    def test_datos_invalidos_no_se_grafican_y_se_informan(self):
        datos = [{'_id':'a','fecha':'sin fecha','temperatura':32,'humedad':60},
                 {'_id':'b','fecha':'2026-10-02T16:00:00Z','temperatura':'nan','humedad':101}]
        figura = Figure(figsize=(8,3), layout='constrained')
        texto = dibujar_graficas(figura, datos)
        self.assertEqual(preparar_serie(datos, 'temperatura'), [])
        self.assertIn('2 registros sin datos válidos', texto)
        FigureCanvasAgg(figura).draw()


if __name__ == '__main__':
    unittest.main(verbosity=2)
