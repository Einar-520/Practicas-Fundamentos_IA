"""Pruebas de contratos, reglas del profesor, respaldo y evidencia auditable."""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from unittest.mock import Mock

import mongomock
from pydantic import ValidationError
from comun.ollama_local import OllamaLocal, ErrorLLM
from tutor.servicio import TutorSQL
from logismart.dominio.modelos import (Configuracion, Premisas, Clasificacion, Correo, Riesgo,
                                     Camion, validar)
from logismart.dominio.reglas import evaluar_camion, decidir, tablas
from logismart.dominio.clasificacion import clasificar_reglas, fusionar
from logismart.infraestructura.repositorio import DemoRepositorio, MongoRepositorio, ErrorDatos, AMBITO, rango_fechas
from logismart.servicios.clasificador import ClasificadorHibrido
from logismart.servicios.aplicacion import Aplicacion
from logismart.servicios.asistente import responder
from logismart.servicios.demostracion import cargar_demo
from logismart.servicios.evaluacion import evaluar_corpus, cargar_corpus, metricas
from logismart.servicios.reportes import exportar, valor_celda

RAIZ = Path(__file__).resolve().parents[1]
CORREO = Correo(remitente='operador@ejemplo.test', asunto='Urgente: derrame en andén 3',
                cuerpo='El CAM-102 con placas ABC-123-D presenta fuga de químico inflamable. Peso: 48.5 toneladas.')


class LLMFalso:
    modelo = 'doble_de_prueba_no_es_llm_real'
    def __init__(self, respuestas):
        self.respuestas = iter(respuestas)
        self.llamadas = []
    def chat(self, mensajes, esquema=None):
        self.llamadas.append((copy.deepcopy(mensajes), esquema))
        respuesta = next(self.respuestas)
        if isinstance(respuesta, Exception): raise respuesta
        return respuesta, 1.0


class TestReglas(unittest.TestCase):
    def test_tabla_original_independiente(self):
        esperado = [(0,1),(0,1),(0,1),(0,1),(1,1),(0,1),(1,0),(0,0)] + [(0,0)] * 8
        for entrada, salida in zip(product((True, False), repeat=4), esperado):
            with self.subTest(entrada=entrada):
                r = evaluar_camion(*entrada)
                self.assertEqual(tuple(r.values()), tuple(map(bool, salida)))

    def test_rechaza_booleanos_ambiguos(self):
        for valor in (1, 'si', None):
            with self.subTest(valor=valor), self.assertRaises(TypeError):
                evaluar_camion(valor, False, False, True)

    def test_tablas_nuevas(self):
        t = tablas()
        self.assertEqual([r['B'] for r in t['B = R ∧ ¬H']], [False, True, False, False])
        self.assertEqual([r['F'] for r in t['F = P ∧ T']], [True, False, False, False])
        self.assertEqual(len(t['A y E']), 16)

    def test_prioridad_inspeccion_sin_cambiar_A(self):
        r = decidir(Premisas(P=True, Q=False, R=True, S=True))
        self.assertTrue(r['A']); self.assertTrue(r['E'])
        self.assertEqual(r['resultado'], 'inspeccion')

    def test_bloqueos(self):
        base = dict(P=True, Q=False, R=False, S=True, H=True, T=False)
        for cambio, esperado in [({'P':False},'denegado'), ({'S':False},'denegado'),
                                 ({'R':True,'H':False},'retenido'), ({'T':True},'retenido')]:
            self.assertEqual(decidir(Premisas(**{**base, **cambio}))['resultado'], esperado)

    def test_riesgo_no_acepta_bool_como_entero(self):
        with self.assertRaises(ValidationError):
            Riesgo(modulo='LLM', descripcion='Alucinación', categoria='seguridad', probabilidad=True,
                   impacto=5, mitigacion='Revisión manual', probabilidad_residual=2, impacto_residual=5, evidencia='Prueba unitaria')


class TestClasificador(unittest.TestCase):
    def test_extraccion_original(self):
        r = clasificar_reglas(CORREO)
        self.assertEqual((r.categoria, r.prioridad), ('materiales_peligrosos', 'critica'))
        self.assertEqual(r.entidades.peso_reportado_kg, 48500)
        self.assertEqual(r.entidades.camion_id, 'CAM-102')
        self.assertEqual(r.entidades.ubicacion, 'andén 3')

    def test_json_valido(self):
        esperado = clasificar_reglas(CORREO).model_dump_json()
        motor = ClasificadorHibrido(LLMFalso([esperado]))
        r = motor.clasificar(CORREO)
        self.assertEqual(set(r['llm']), {'categoria', 'prioridad', 'entidades', 'resumen'})
        self.assertFalse(r['requiere_revision_humana'])
        self.assertEqual(r['intentos'][0]['estado'], 'valido')

    def test_reintento_y_respaldo(self):
        cliente = LLMFalso(['no es JSON', '{"categoria":"otro"}'])
        r = ClasificadorHibrido(cliente).clasificar(CORREO)
        self.assertEqual(len(cliente.llamadas), 2)
        self.assertIsNone(r['llm'])
        self.assertEqual(r['clasificacion']['prioridad'], 'critica')
        self.assertTrue(r['requiere_revision_humana'])

    def test_recuperacion_segundo_intento(self):
        valido = clasificar_reglas(CORREO).model_dump_json()
        r = ClasificadorHibrido(LLMFalso(['{}', valido])).clasificar(CORREO)
        self.assertIsNotNone(r['llm'])
        self.assertEqual([i['estado'] for i in r['intentos']], ['json_invalido', 'valido'])

    def test_claves_extra_y_tipos_estrictos(self):
        for cambio in ({'extra': 'atajo'}, {'entidades': {'placa': None, 'camion_id': None, 'peso_reportado_kg': '1000', 'ubicacion': None}}):
            datos = {**clasificar_reglas(CORREO).model_dump(), **cambio}
            r = ClasificadorHibrido(LLMFalso([json.dumps(datos)] * 2)).clasificar(CORREO)
            self.assertIsNone(r['llm'])

    def test_sin_servidor(self):
        cliente = LLMFalso([ErrorLLM('Sin conexión')])
        r = ClasificadorHibrido(cliente).clasificar(CORREO)
        self.assertEqual(len(cliente.llamadas), 1)
        self.assertEqual(r['origen'], 'respaldo_reglas')

    def test_fusion_no_reduce_prioridad(self):
        reglas = clasificar_reglas(CORREO)
        llm = reglas.model_copy(update={'categoria': 'otro', 'prioridad': 'baja'})
        fusion, revision = fusionar(reglas, llm)
        self.assertEqual(fusion.prioridad, 'critica'); self.assertTrue(revision)
        fusion, revision = fusionar(llm, reglas)
        self.assertEqual(fusion.prioridad, 'critica'); self.assertTrue(revision)

    def test_llm_no_inventa_entidades_persistidas(self):
        reglas = clasificar_reglas(CORREO)
        inventado = reglas.model_copy(deep=True)
        inventado.entidades.placa = 'ZZZ-999-Z'
        fusion, revision = fusionar(reglas, inventado)
        self.assertEqual(fusion.entidades.placa, 'ABC-123-D'); self.assertTrue(revision)

    def test_ollama_solo_local(self):
        for url in ['https://externo.example', 'http://otro.example:11434', 'http://user:clave@localhost:11434', 'http://localhost/ruta']:
            with self.subTest(url=url), self.assertRaises(ValueError): OllamaLocal(url=url)


class RepositorioCasos:
    def test_CRUD_y_versiones(self):
        original = self.repo.crear('riesgos_eticos', {'descripcion': 'Inicial'}, 'Operador')
        editado = self.repo.actualizar('riesgos_eticos', original['_id'], {'descripcion': 'Corregida'}, 'Otro', 1, 'Corrección')
        self.assertEqual(editado['version'], 2)
        self.assertEqual(editado['historico'][-1]['anterior']['descripcion'], 'Inicial')
        with self.assertRaises(ErrorDatos):
            self.repo.actualizar('riesgos_eticos', original['_id'], {'descripcion':'Fuera de fecha'}, 'Otro', 1, 'Cambio')
        self.repo.eliminar('riesgos_eticos', original['_id'], 'Operador', 2)
        self.assertEqual(self.repo.listar('riesgos_eticos'), [])

    def test_no_permite_sobrescribir_ambito(self):
        with self.assertRaises(ValueError):
            self.repo.crear('camiones', {'alumno': 'Otra persona'}, 'Operador')

    def test_placa_unica(self):
        d = dict(placa='ABC-123-D', camion_id='CAM-102')
        self.repo.crear('camiones', d, 'Operador')
        with self.assertRaises(ErrorDatos): self.repo.crear('camiones', {**d, 'camion_id': 'CAM-999'}, 'Operador')

    def test_rango_de_fechas(self):
        self.repo.crear('accesos', {'dato':1}, 'Operador')
        self.assertEqual(self.repo.listar('accesos', desde='2000-01-01', hasta='2001-01-01'), [])
        with self.assertRaises(ValueError): self.repo.listar('accesos', desde='2026-12-01', hasta='2026-01-01')


class TestDemo(RepositorioCasos, unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = DemoRepositorio(Path(self.tmp.name) / 'datos.json')

    def test_persistencia_en_archivo(self):
        self.repo.crear('accesos', {'dato': 1}, 'Operador')
        otro = DemoRepositorio(self.repo.ruta)
        self.assertEqual(len(otro.listar('accesos')), 1)

    def test_errores_de_escritura_no_modifican_memoria(self):
        self.repo._guardar = Mock(side_effect=OSError('Sin espacio'))
        with self.assertRaises(ErrorDatos): self.repo.crear('incidentes', {'dato':1}, 'Operador')
        self.assertEqual(self.repo.listar('incidentes'), [])

    def test_semana_iso_con_cambio_de_anio(self):
        d = self.repo.crear('incidentes', {'clasificacion': {'categoria':'otro'}}, 'Operador')
        self.repo.datos['incidentes'][0]['creado_en'] = '2021-01-01T12:00:00+00:00'
        self.assertEqual(self.repo.agregar_incidentes(), [{'anio':2020,'semana':53,'categoria':'otro','total':1}])


class TestMongo(RepositorioCasos, unittest.TestCase):
    def setUp(self):
        self.cliente = mongomock.MongoClient(tz_aware=True)
        self.repo = MongoRepositorio('mongodb://127.0.0.1:27017/', 'prueba', self.cliente)
        self.repo.comprobar()

    def test_aislamiento(self):
        self.repo.db.accesos.insert_one({'_id':'ajeno','proyecto':'otro','alumno':'Otra persona','eliminado':False,'version':1})
        self.assertEqual(self.repo.listar('accesos'), [])
        with self.assertRaises(ErrorDatos): self.repo.eliminar('accesos','ajeno','Operador',1)
        self.assertFalse(self.repo.db.accesos.find_one({'_id':'ajeno'})['eliminado'])

    def test_agregacion_se_envia_a_mongodb(self):
        agregado = Mock(return_value=[{'_id':{'anio':2026,'semana':40,'categoria':'otro'},'total':2}])
        self.repo.db.incidentes.aggregate = agregado
        self.assertEqual(self.repo.agregar_incidentes()[0]['total'], 2)
        pipeline = agregado.call_args.args[0]
        self.assertEqual(pipeline[0]['$match'], {**AMBITO, 'eliminado':False})
        self.assertEqual(pipeline[1]['$group']['_id']['semana'], {'$isoWeek':'$creado_en'})


class TestServicio(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo = DemoRepositorio(Path(self.tmp.name) / 'demo.json')
        self.motor = ClasificadorHibrido(LLMFalso([]), False)
        self.app = Aplicacion(self.repo, self.motor, Configuracion(usar_llm=False))
        cargar_demo(self.app)

    def test_demo_idempotente(self):
        self.assertTrue(cargar_demo(self.app).startswith('0 registros'))
        self.assertEqual(self.app.panel()['camiones_atendidos'], 4)

    def test_vigencia(self):
        self.assertFalse(self.app.buscar_placa('abc-104-d')['S'])
        self.assertTrue(self.app.buscar_placa('abc-101-d')['S'])

    def test_historial_correccion_incidente(self):
        d = self.repo.listar('incidentes')[0]
        e = self.app.editar_incidente({'categoria':'otro','prioridad':'baja','estado':'cerrado',
            'resumen':'Resuelto por supervisor','requiere_revision_humana':False,'motivo':'Comprobación del operador'}, d)
        self.assertEqual(e['estado'], 'cerrado')
        self.assertEqual(e['historico'][-1]['anterior']['estado'], 'nuevo')

    def test_asistente_sin_datos_no_llama_llm(self):
        cliente = LLMFalso([])
        r = responder(self.repo, cliente, '¿Por qué CAM-999 pasó?', 'Operador')
        self.assertIn('No tengo información', r['respuesta_mostrada'])
        self.assertEqual(cliente.llamadas, [])

    def test_asistente_rechaza_fuente_inventada(self):
        cliente = LLMFalso(['{"fuentes":["accesos:inventado"]}'])
        r = responder(self.repo, cliente, '¿Por qué CAM-102 fue a inspección?', 'Operador')
        self.assertEqual(r['estado'], 'respaldo_extractivo')
        self.assertIn('inspeccion', r['respuesta_mostrada'])
        self.assertNotIn('inventado', r['respuesta_mostrada'])
        self.assertTrue(r['fuentes'][0].startswith('accesos:'))

    def test_asistente_cita_fuente_real(self):
        d = self.repo.listar('accesos', {'camion_id':'CAM-102'})[0]
        cliente = LLMFalso([json.dumps({'fuentes':[f"accesos:{d['_id']}"]})])
        r = responder(self.repo, cliente, '¿Por qué CAM-102 fue a inspección?', 'Operador')
        self.assertIn(d['_id'], r['respuesta_mostrada'])
        self.assertEqual(r['estado'], 'llm_con_fuentes_validadas')

    def test_asistente_sin_respuesta_pertinente(self):
        cliente = LLMFalso(['{"fuentes":[]}'])
        r = responder(self.repo, cliente, '¿Cuál es el color de CAM-102?', 'Operador')
        self.assertIn('No tengo información', r['respuesta_mostrada'])
        self.assertEqual(r['fuentes'], [])

    def test_CRUD_evaluacion_manual(self):
        d = self.app.guardar_evaluacion_manual(dict(prompt='Pregunta', respuesta='Respuesta', modelo='prueba', latencia_ms=2.0, coincidio_reglas=None, observacion='Ejemplo manual'))
        self.assertEqual(d['tipo'], 'manual')
        self.repo.eliminar('evaluaciones_llm', d['_id'], 'Operador', d['version'])
        self.assertEqual(self.repo.listar('evaluaciones_llm'), [])

    def test_exportacion_tres_formatos(self):
        for extension in ('pdf','csv','json'):
            destino = Path(self.tmp.name) / ('reporte.' + extension)
            exportar(self.repo.listar('accesos'), destino)
            self.assertGreater(destino.stat().st_size, 100)
        self.assertEqual(valor_celda('=1+1'), "'=1+1")

    def test_corpus_y_resultados_no_fabricados(self):
        ruta = RAIZ/'datos/correos_etiquetados.json'
        corpus = cargar_corpus(ruta)
        self.assertEqual(len(corpus),30)
        r = evaluar_corpus(ruta, self.motor)
        self.assertIsNone(r['metricas']['llm']['exactitud_categoria'])
        self.assertEqual(r['etiquetas_revisadas_por_persona'],0)
        self.assertAlmostEqual(r['metricas']['reglas']['exactitud_categoria'],22/30)
        self.assertEqual(sum(map(sum,r['metricas']['reglas']['matriz_confusion'])),30)


class TestTutor(unittest.TestCase):
    def test_historial_resumen_y_recuperacion(self):
        with tempfile.TemporaryDirectory() as tmp:
            tutor = TutorSQL(LLMFalso(['SELECT titulo FROM libros;']), Path(tmp)/'historial.json')
            tutor.preguntar('¿Cómo consulto los libros?')
            tutor.cliente = LLMFalso([ErrorLLM('Sin conexión'), ErrorLLM('Sin conexión')])
            with self.assertRaises(ErrorLLM): tutor.preguntar('Otra consulta')
            self.assertEqual(len(tutor.historial),2)
            self.assertIn('Resumen local', tutor.resumir())
            self.assertEqual(len(TutorSQL(LLMFalso([]), tutor.ruta).historial),2)


if __name__ == '__main__':
    unittest.main()
