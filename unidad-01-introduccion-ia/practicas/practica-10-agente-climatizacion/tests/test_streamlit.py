"""Probar la interfaz real de Streamlit con una colección aislada en memoria."""

from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import pandas as pd
import pyarrow as pa
from streamlit.testing.v1 import AppTest

DIRECTORIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DIRECTORIO))
from agente_climatizacion import ACCIONES, AgenteClimatizacion
import almacenamiento_atlas as atlas
import interfaz
from test_practica10 import ColeccionSimulada


def graficas(app):
    # El nombre del elemento cambió entre versiones de Streamlit.
    return [e for e in app.main if e.type.endswith('vega_lite_chart')]


def pulsar(app, texto):
    return next(boton for boton in app.button if boton.label == texto).click().run()


class GraficasTest(unittest.TestCase):
    def test_tabla_y_graficas_conservan_ids_valores_y_fechas(self):
        registros = [
            {'_id': 'b', 'fecha': '2026-09-23T11:30:00+00:00', 'temperatura': 34.5,
             'humedad': 65, 'accion': ACCIONES[1]},
            {'_id': 'a', 'fecha': '2026-09-23T05:00:00-06:00', 'temperatura': 31,
             'humedad': 60, 'accion': ACCIONES[1]},
        ]
        original = deepcopy(registros)
        tabla = interfaz.preparar_tabla(registros)
        for variable in ['Temperatura (°C)', 'Humedad (%)']:
            grafica = interfaz.crear_grafica(tabla, variable, '#167d98').to_dict()
            datos = next(iter(grafica['datasets'].values()))
            self.assertEqual([r['ID'] for r in datos], ['a', 'b'])
            self.assertEqual({r['Acción'] for r in datos}, {ACCIONES[1]})
            self.assertEqual(grafica['encoding']['x']['scale']['type'], 'utc')
            self.assertTrue(grafica['mark']['point'])
        self.assertEqual(registros, original)
        self.assertEqual(tabla.iloc[1]['Fecha (UTC)'].hour, 11)

    def test_vacios_y_datos_invalidos_no_inventan_mediciones(self):
        self.assertTrue(interfaz.preparar_tabla([]).empty)
        registros = [{'_id': 'x', 'fecha': 'sin fecha', 'temperatura': 'NaN', 'humedad': 'inf', 'accion': ACCIONES[0]}]
        tabla = interfaz.preparar_tabla(registros)
        self.assertTrue(pd.isna(tabla.iloc[0]['Temperatura (°C)']))
        self.assertTrue(pd.isna(tabla.iloc[0]['Humedad (%)']))
        self.assertTrue(pd.isna(tabla.iloc[0]['Fecha (UTC)']))
        self.assertEqual(tabla.iloc[0]['ID'], 'x')


class InterfazStreamlitTest(unittest.TestCase):
    def setUp(self):
        self.coleccion = ColeccionSimulada()
        fabrica = patch.object(interfaz, 'AlmacenamientoAtlas',
                               side_effect=lambda: atlas.AlmacenamientoAtlas(self.coleccion))
        fabrica.start()
        self.addCleanup(fabrica.stop)
        # Si alguna ruta olvidara el sustituto, la prueba falla antes de conectar.
        red = patch.object(atlas, 'MongoClient', side_effect=AssertionError('La prueba no debe abrir Atlas real'))
        red.start()
        self.addCleanup(red.stop)
        self.app = AppTest.from_file(str(DIRECTORIO / '10_agente_climatizacion.py'), default_timeout=15)

    def insertar(self, temperatura, humedad):
        agente = AgenteClimatizacion()
        agente.percibir(temperatura, humedad)
        return agente.ejecutar(atlas.AlmacenamientoAtlas(self.coleccion))['_id']

    def ejecutar(self):
        self.app.run()
        self.assertEqual(len(self.app.exception), 0)
        return self.app

    def filtrar(self, accion):
        self.app.selectbox(key='filtro_accion').select(accion).run()
        self.assertEqual(len(self.app.exception), 0)

    def seleccionar(self, modo, identificador):
        self.app.radio(key='operacion').set_value(modo).run()
        next(s for s in self.app.selectbox if s.label == 'Registro').select(identificador).run()

    def test_filtrar_accion_tabla_y_graficas_sin_escrituras(self):
        ventilador = self.insertar(32, 60)
        self.insertar(35, 80)
        self.insertar(16, 40)
        self.insertar(25, 40)
        self.ejecutar()
        self.assertEqual(len(self.app.dataframe[0].value), 4)
        for accion in ACCIONES:
            self.filtrar(accion)
            self.assertEqual(set(self.app.dataframe[0].value['Acción']), {accion})
            self.assertEqual(len(graficas(self.app)), 2)
            tabla = self.app.dataframe[0].value
            for grafica in graficas(self.app):
                datos = pa.ipc.open_stream(grafica.proto.datasets[0].data.data).read_all().to_pandas()
                self.assertEqual(set(datos['ID']), set(tabla['ID']))
                self.assertEqual(set(datos['Acción']), {accion})
                for variable in ['Temperatura (°C)', 'Humedad (%)']:
                    self.assertEqual(datos.set_index('ID')[variable].to_dict(), tabla.set_index('ID')[variable].to_dict())
            elementos = [e.type for e in self.app.main]
            self.assertLess(elementos.index('selectbox'), elementos.index('dataframe'))
            indice_grafica = next(i for i, tipo in enumerate(elementos) if tipo.endswith('vega_lite_chart'))
            self.assertLess(elementos.index('dataframe'), indice_grafica)
        self.filtrar(ACCIONES[1])
        self.assertEqual(self.app.dataframe[0].value['ID'].tolist(), [ventilador])
        self.filtrar(interfaz.TODAS)
        self.assertEqual(len(self.app.dataframe[0].value), 4)
        self.assertEqual(self.coleccion.llamadas, 4)

    def test_crear_con_decimales_y_reejecutar_no_duplica(self):
        self.ejecutar()
        self.app.text_input[0].set_value('32,5')
        self.app.text_input[1].set_value('60')
        pulsar(self.app, 'Crear registro')
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.coleccion.registros), 1)
        self.assertEqual(self.coleccion.registros[0]['accion'], ACCIONES[1])
        self.assertEqual(self.coleccion.registros[0]['temperatura'], 32.5)
        self.app.run()
        pulsar(self.app, 'Actualizar registros')
        self.assertEqual(self.coleccion.llamadas, 1)
        self.assertEqual(len(self.app.dataframe[0].value), 1)

    def test_entrada_invalida_no_guarda_y_conserva_el_formulario(self):
        self.ejecutar()
        self.app.text_input[0].set_value('32')
        self.app.text_input[1].set_value('101')
        pulsar(self.app, 'Crear registro')
        self.assertEqual(self.coleccion.llamadas, 0)
        self.assertEqual(self.app.text_input[1].value, '101')
        self.assertTrue(any('humedad' in e.value for e in self.app.error))

    def test_editar_recalcula_accion_y_sale_del_filtro_activo(self):
        identificador = self.insertar(32, 60)
        fecha = self.coleccion.registros[0]['fecha']
        self.ejecutar()
        self.filtrar(ACCIONES[1])
        self.seleccionar('Editar', identificador)
        self.app.text_input[0].set_value('25')
        pulsar(self.app, 'Guardar cambios')
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.coleccion.registros[0]['accion'], ACCIONES[3])
        self.assertEqual(self.coleccion.registros[0]['fecha'], fecha)
        self.assertEqual(str(self.coleccion.registros[0]['_id']), identificador)
        self.assertEqual(len(self.app.dataframe), 0)
        self.assertEqual(len(graficas(self.app)), 0)
        self.assertTrue(any('Para verlo' in aviso.value for aviso in self.app.success))
        self.filtrar(ACCIONES[3])
        self.assertEqual(self.app.dataframe[0].value['ID'].tolist(), [identificador])

    def test_eliminar_exige_confirmacion_y_borra_el_id_seleccionado(self):
        primero = self.insertar(32, 60)
        segundo = self.insertar(34, 50)
        self.ejecutar()
        self.seleccionar('Eliminar', primero)
        pulsar(self.app, 'Eliminar registro')
        self.assertEqual(len(self.coleccion.registros), 2)
        self.app.checkbox[0].check()
        pulsar(self.app, 'Eliminar registro')
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual([str(r['_id']) for r in self.coleccion.registros], [segundo])
        self.assertEqual(self.app.dataframe[0].value['ID'].tolist(), [segundo])

    def test_paginacion_filtro_vacio_y_cambio_de_seleccion(self):
        for _ in range(atlas.TAMANO_PAGINA + 2):
            self.insertar(32, 60)
        self.insertar(16, 30)
        self.ejecutar()
        pulsar(self.app, 'Siguiente')
        self.assertEqual(len(self.app.dataframe[0].value), 3)
        self.filtrar(ACCIONES[1])
        self.assertEqual(self.app.session_state['pagina'], 0)
        self.assertEqual(len(self.app.dataframe[0].value), 50)
        identificador = self.app.dataframe[0].value.iloc[0]['ID']
        self.seleccionar('Eliminar', identificador)
        self.filtrar(ACCIONES[2])
        self.assertIsNone(next(s for s in self.app.selectbox if s.label == 'Registro').value)
        self.filtrar(ACCIONES[0])
        self.assertEqual(len(self.app.dataframe), 0)
        self.assertEqual(len(graficas(self.app)), 0)
        self.assertTrue(any('No hay registros' in aviso.value for aviso in self.app.info))

    def test_errores_de_consulta_ocultan_datos_antiguos_y_no_exponen_secretos(self):
        self.insertar(32, 60)
        self.ejecutar()
        self.coleccion.fallo_lectura = True
        self.filtrar(ACCIONES[2])
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.dataframe), 0)
        self.assertEqual(len(graficas(self.app)), 0)
        self.assertEqual(len(self.app.text_input), 0)
        self.assertTrue(self.app.error)
        self.assertFalse(any('CREDENCIAL' in e.value for e in self.app.error))
        self.coleccion.fallo_lectura = False
        pulsar(self.app, 'Actualizar registros')
        self.assertEqual(len(self.app.error), 0)

    def test_escritura_confirmada_con_refresco_fallido_no_se_repite(self):
        self.ejecutar()
        self.coleccion.fallo_lectura = True
        self.app.text_input[0].set_value('32')
        self.app.text_input[1].set_value('60')
        pulsar(self.app, 'Crear registro')
        self.assertEqual(len(self.app.exception), 0)
        self.assertTrue(any('confirmados por Atlas' in e.value for e in self.app.success))
        self.assertTrue(self.app.error)
        self.assertEqual(len(self.coleccion.registros), 1)
        self.app.run()
        self.assertEqual(self.coleccion.llamadas, 1)
        self.coleccion.fallo_lectura = False
        pulsar(self.app, 'Actualizar registros')
        self.assertEqual(len(self.app.dataframe[0].value), 1)

    def test_escritura_incierta_no_se_reintenta_hasta_consultar(self):
        self.ejecutar()
        self.coleccion.fallo_despues_de_insertar = True
        self.app.text_input[0].set_value('32')
        self.app.text_input[1].set_value('60')
        pulsar(self.app, 'Crear registro')
        self.assertEqual(len(self.app.success), 0)
        self.assertTrue(any('no se confirmó' in e.value for e in self.app.error))
        self.app.run()
        self.assertEqual(self.coleccion.llamadas, 1)
        self.assertEqual(len(self.app.text_input), 0)
        self.coleccion.fallo_despues_de_insertar = False
        pulsar(self.app, 'Actualizar registros')
        self.assertEqual(len(self.app.dataframe[0].value), 1)
        self.assertEqual(self.coleccion.llamadas, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
