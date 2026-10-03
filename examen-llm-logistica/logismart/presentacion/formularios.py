"""Formularios específicos de las cinco colecciones del examen."""
from datetime import datetime
from zoneinfo import ZoneInfo
from tkinter import ttk, messagebox
from logismart.presentacion.componentes import Formulario, texto_detalle
from logismart.dominio.modelos import CATEGORIAS, PRIORIDADES, ESTADOS, CATEGORIAS_ETICAS, Premisas
from logismart.dominio.reglas import decidir


def guardar_formulario(app, pagina, formulario, tarea):
    def terminado(registro):
        formulario.destroy()
        app.estado.set(f"Registro guardado: {registro['_id']}")
        pagina.actualizar()
    app.trabajos.ejecutar('Validando y guardando…', tarea, terminado)


def camion(app, pagina, anterior):
    campos = [('placa', 'Placa (5–15 caracteres)', 'cadena', None),
              ('camion_id', 'Identificador (CAM-102)', 'cadena', None),
              ('empresa', 'Empresa', 'cadena', None),
              ('autorizacion', 'Autorización previa', 'bool', None),
              ('certificacion_conductor', 'Conductor certificado', 'bool', None),
              ('certificado_id', 'Folio del certificado', 'cadena', None),
              ('certificacion_hasta', 'Vigencia hasta (AAAA-MM-DD)', 'cadena', None)]
    Formulario(app, 'Camión', campos, anterior or {},
               lambda f, d: guardar_formulario(app, pagina, f, lambda: app.servicio.guardar_camion(d, anterior)))


def acceso(app, pagina, anterior):
    campos = [('camion_id', 'Identificador (CAM-102)', 'cadena', None), ('placa', 'Placa', 'cadena', None),
              ('P', 'P: autorización previa', 'bool', None), ('Q', 'Q: exceso de peso', 'bool', None),
              ('R', 'R: materiales peligrosos', 'bool', None), ('S', 'S: certificación vigente', 'bool', None),
              ('H', 'H: horario permitido', 'bool', None), ('T', 'T: alerta de fatiga', 'bool', None),
              ('observacion', 'Observaciones de la captura manual', 'texto', None),
              ('motivo', 'Motivo de corrección (si editas)', 'cadena', None)]
    hora = datetime.now(ZoneInfo('America/Mexico_City')).hour
    valores = anterior or {'H': app.config.hora_inicio <= hora < app.config.hora_fin, 'T': False}

    def extra(f):
        ttk.Label(f.extra, text='Confirma las premisas. La búsqueda carga P y S desde el camión registrado.', wraplength=620).pack(anchor='w')
        semaforo = ttk.Label(f.extra, font=('TkDefaultFont', 14, 'bold'))
        semaforo.pack(anchor='w', pady=8)
        explicacion = ttk.Label(f.extra, wraplength=620, justify='left')
        explicacion.pack(anchor='w')

        def previsualizar(*_):
            p = Premisas(**{k: f.variables[k].get() for k in 'PQRSTH'})
            resultado = decidir(p)
            colores = {'rojo': '#b91c1c', 'amarillo': '#8a5700', 'verde': '#15803d'}
            semaforo.configure(text=f"{resultado['resultado'].upper()} · A={resultado['A']} · E={resultado['E']}", foreground=colores[resultado['semaforo']])
            explicacion.configure(text='\n'.join(resultado['explicacion']))
        for k in 'PQRSTH': f.variables[k].trace_add('write', previsualizar)

        def buscar():
            placa = f.variables['placa'].get()
            def encontrado(d):
                for k in ('placa', 'camion_id', 'P', 'S'): f.variables[k].set(d[k])
            app.trabajos.ejecutar('Buscando placa y vigencia…', lambda: app.servicio.buscar_placa(placa), encontrado)
        ttk.Button(f.extra, text='Buscar por placa y cargar autorización/certificación', command=buscar).pack(anchor='w', pady=8)
        previsualizar()
    Formulario(app, 'Control de acceso', campos, valores,
               lambda f, d: guardar_formulario(app, pagina, f, lambda: app.servicio.guardar_acceso(d, anterior)), extra)


def riesgo(app, pagina, anterior):
    campos = [('modulo', 'Módulo', 'cadena', None), ('descripcion', 'Descripción del riesgo', 'texto', None),
              ('categoria', 'Categoría ética', 'opcion', CATEGORIAS_ETICAS),
              ('probabilidad', 'Probabilidad inicial (1–5)', 'entero', None),
              ('impacto', 'Impacto inicial (1–5)', 'entero', None),
              ('mitigacion', 'Mitigación', 'texto', None),
              ('probabilidad_residual', 'Probabilidad residual (1–5)', 'entero', None),
              ('impacto_residual', 'Impacto residual (1–5)', 'entero', None),
              ('evidencia', 'Evidencia o referencia a prueba', 'texto', None)]
    valores = anterior or {'probabilidad': 3, 'impacto': 3, 'probabilidad_residual': 2, 'impacto_residual': 3}
    Formulario(app, 'Riesgo ético', campos, valores,
               lambda f, d: guardar_formulario(app, pagina, f, lambda: app.servicio.guardar_riesgo(d, anterior)))


def incidente(app, pagina, anterior):
    if anterior:
        campos = [('categoria', 'Categoría', 'opcion', CATEGORIAS), ('prioridad', 'Prioridad', 'opcion', PRIORIDADES),
                  ('estado', 'Estado', 'opcion', ESTADOS), ('resumen', 'Resumen', 'texto', None),
                  ('requiere_revision_humana', 'Pendiente de revisión humana', 'bool', None),
                  ('placa', 'Placa extraída (opcional)', 'opcional', None),
                  ('camion_id', 'Camión extraído (opcional)', 'opcional', None),
                  ('peso_reportado_kg', 'Peso extraído en kg (opcional)', 'decimal_opcional', None),
                  ('ubicacion', 'Ubicación extraída (opcional)', 'opcional', None),
                  ('motivo', 'Motivo de la corrección (mín. 5 caracteres)', 'texto', None)]
        valores = {**anterior['clasificacion'], **anterior['datos_extraidos'], 'estado': anterior['estado'],
                   'requiere_revision_humana': anterior['requiere_revision_humana']}
        Formulario(app, 'Revisión humana del incidente', campos, valores,
                   lambda f, d: guardar_formulario(app, pagina, f, lambda: app.servicio.editar_incidente(d, anterior)))
    else:
        campos = [('remitente', 'Remitente', 'cadena', None), ('asunto', 'Asunto', 'cadena', None),
                  ('cuerpo', 'Pega el correo (máx. 10 000 caracteres)', 'texto', None)]
        Formulario(app, 'Clasificar y guardar correo', campos, {'remitente': 'operador@ejemplo.test'},
                   lambda f, d: guardar_formulario(app, pagina, f, lambda: app.servicio.clasificar_correo(d)))


def evaluacion(app, pagina, anterior):
    campos = [('prompt', 'Prompt o solicitud', 'texto', None), ('respuesta', 'Respuesta registrada', 'texto', None),
              ('modelo', 'Modelo', 'cadena', None), ('latencia_ms', 'Latencia (ms)', 'decimal', None),
              ('coincidio', '¿Coincidió con las reglas?', 'opcion', ('No evaluado', 'Sí', 'No')),
              ('observacion', 'Motivo / observación manual (mín. 5 caracteres)', 'texto', None)]
    valores = dict(anterior or {'modelo': app.config.modelo, 'latencia_ms': 0})
    valores['coincidio'] = {True: 'Sí', False: 'No', None: 'No evaluado'}[valores.get('coincidio_reglas')]
    def guardar(f, datos):
        datos['coincidio_reglas'] = {'Sí': True, 'No': False, 'No evaluado': None}[datos.pop('coincidio')]
        guardar_formulario(app, pagina, f, lambda: app.servicio.guardar_evaluacion_manual(datos, anterior))
    Formulario(app, 'Evaluación LLM · corrección manual identificada', campos, valores, guardar)
