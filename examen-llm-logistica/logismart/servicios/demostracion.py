"""Datos ficticios e idempotentes, cargados solamente cuando el usuario lo pide."""
from datetime import date, timedelta
from logismart.dominio.clasificacion import clasificar_reglas
from logismart.dominio.modelos import Correo

RIESGOS_DEMO = [
    ('Asistente LLM', 'El modelo inventa causas o registros al explicar un acceso.', 'transparencia', 4, 5,
     'RAG extractivo, lista de fuentes permitidas y respuesta sin datos cuando no existe evidencia.', 2, 5,
     'Pruebas de fuente inexistente, contexto vacío y respuesta inyectada; test_asistente.'),
    ('Clasificador de correos', 'Subclasificación de incidentes escritos con ortografía informal.', 'sesgo', 4, 5,
     'Comparar exactitud formal/informal y revisar manualmente discrepancias, sin respuesta u otro.', 3, 4,
     'Corpus COR-004, COR-008, COR-012 y comparación por registro. Residual estimado, no certificado.'),
    ('MongoDB y reportes', 'Exposición de datos de conductores y correos mediante prompts, reportes o credenciales.', 'privacidad', 4, 4,
     'LLM solo en loopback, .env excluido, mínimo de datos del conductor y acceso limitado a base y alumno.', 2, 4,
     'Validación de URL local, prueba de ámbito y revisión de archivos publicados. Falta auditar permisos reales de Atlas.'),
    ('Control de acceso', 'El operador confía en la automatización sin comprobar sensores ni vigencias.', 'responsabilidad', 4, 5,
     'Premisas visibles, explicación por pasos, prioridad de inspección y confirmación de captura por operador.', 3, 4,
     'Tabla completa A/E y prueba del caso A=E=verdadero. Formación del operador pendiente.'),
    ('Entrada LLM', 'Instrucciones maliciosas en un correo alteran la clasificación.', 'seguridad', 4, 4,
     'Contrato Pydantic estricto, prompt que trata el correo como datos y fusión con la prioridad mayor.', 2, 4,
     'Pruebas de JSON inválido, claves extra y reintento; el esquema no garantiza verdad semántica.'),
    ('Auditoría', 'La edición o eliminación oculta la decisión original.', 'responsabilidad', 3, 4,
     'Control de versión, historial con valor anterior y bajas lógicas. Restringir acceso directo a MongoDB.', 2, 4,
     'Pruebas de edición concurrente y baja lógica; un administrador de MongoDB aún puede alterar datos.'),
]


def cargar_demo(servicio):
    repo, operador = servicio.repo, servicio.config.operador
    creados = 0
    for numero, autorizado, certificado in [(101, True, True), (102, True, True), (103, False, True), (104, True, False)]:
        identificador = f'CAM-{numero}'
        if not repo.listar('camiones', {'camion_id': identificador}):
            servicio.guardar_camion({'placa': f'ABC-{numero}-D', 'camion_id': identificador,
                'empresa': 'Transportes Demostración', 'autorizacion': autorizado,
                'certificacion_conductor': certificado, 'certificado_id': f'CERT-DEMO-{numero}',
                'certificacion_hasta': (date.today() + timedelta(days=365 if certificado else -30)).isoformat()})
            creados += 1
    for numero, p in [(101, (True, False, False, True, True, False)),
                      (102, (True, False, True, True, True, False)),
                      (103, (False, False, False, True, True, False)),
                      (104, (True, False, False, False, True, True))]:
        if not repo.listar('accesos', {'camion_id': f'CAM-{numero}'}):
            servicio.guardar_acceso({**dict(zip(('P', 'Q', 'R', 'S', 'H', 'T'), p)),
                'camion_id': f'CAM-{numero}', 'placa': f'ABC-{numero}-D', 'observacion': 'Dato ficticio de demostración.'})
            creados += 1
    for modulo, descripcion, categoria, p, i, mitigacion, pr, ir, evidencia in RIESGOS_DEMO:
        if not repo.listar('riesgos_eticos', {'descripcion': descripcion}):
            servicio.guardar_riesgo(dict(modulo=modulo, descripcion=descripcion, categoria=categoria,
                probabilidad=p, impacto=i, mitigacion=mitigacion, probabilidad_residual=pr,
                impacto_residual=ir, evidencia=evidencia))
            creados += 1
    ejemplos = [
        ('DEMO-1', 'Fuga en andén 3', 'El CAM-102 con placas ABC-102-D tiene una fuga de líquido inflamable.'),
        ('DEMO-2', 'Sobrepeso', 'La báscula del CAM-101 indica 52 toneladas y sobrepeso.'),
        ('DEMO-3', 'Falla de lector', 'El lector RFID no enciende en puerta B.'),
    ]
    for demo_id, asunto, cuerpo in ejemplos:
        if not repo.listar('incidentes', {'demo_id': demo_id}):
            correo = Correo(remitente='operador@demostracion.test', asunto=asunto, cuerpo=cuerpo)
            clasificacion = clasificar_reglas(correo).model_dump()
            repo.crear('incidentes', {'demo_id': demo_id, 'correo_original': correo.model_dump(),
                'clasificacion': clasificacion, 'datos_extraidos': clasificacion['entidades'],
                'estado': 'nuevo', 'requiere_revision_humana': True, 'origen': 'demostracion_solo_reglas',
                'reglas': clasificacion, 'llm': None, 'evaluaciones': []}, operador)
            creados += 1
    return f'{creados} registros ficticios agregados. No se inventaron respuestas ni mediciones del LLM.'
