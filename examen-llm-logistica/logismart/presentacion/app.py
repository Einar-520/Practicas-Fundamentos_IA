"""Ventana principal: capas de dominio e infraestructura se consumen por servicios."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from comun.ollama_local import OllamaLocal
from comun.trabajos_tk import TrabajosTk
from logismart.dominio.modelos import Configuracion, Premisas, validar
from logismart.dominio.reglas import decidir, tablas
from logismart.infraestructura.configuracion import guardar_configuracion, RAIZ
from logismart.infraestructura.repositorio import COLECCIONES
from logismart.servicios.clasificador import ClasificadorHibrido
from logismart.servicios.asistente import responder
from logismart.servicios.reportes import exportar
from logismart.servicios.notificaciones import notificar
from logismart.presentacion.componentes import Tabla, PaginaCRUD, Formulario, texto_detalle
from logismart.presentacion import formularios


class VentanaLogiSmart:
    def __init__(self, servicio):
        self.servicio, self.config = servicio, servicio.config
        self.root = tk.Tk()
        self.root.title('Examen · LogiSmart')
        self.root.geometry('1230x830')
        self.root.minsize(1020, 720)
        cabecera = ttk.Frame(self.root, padding=(16, 12))
        cabecera.pack(fill='x')
        ttk.Label(cabecera, text='LogiSmart', font=('TkDefaultFont', 20, 'bold')).pack(side='left')
        ttk.Label(cabecera, text=f'  {servicio.repo.modo} · Las decisiones requieren supervisión del operador.').pack(side='left')
        pie = ttk.Frame(self.root, padding=10)
        pie.pack(side='bottom', fill='x')
        self.estado = tk.StringVar(value='Listo')
        ttk.Label(pie, textvariable=self.estado).pack(side='left')
        progreso = ttk.Progressbar(pie, mode='indeterminate', length=190)
        progreso.pack(side='right')
        self.trabajos = TrabajosTk(self.root, self.estado, progreso)
        centro = ttk.Frame(self.root)
        centro.pack(fill='both', expand=True)
        self.menu = tk.Listbox(centro, width=24, font=('TkDefaultFont', 12), exportselection=False, activestyle='none')
        self.menu.pack(side='left', fill='y', padx=(12, 0), pady=(0, 12))
        self.contenedor = ttk.Frame(centro)
        self.contenedor.pack(side='left', fill='both', expand=True)
        self.contenedor.columnconfigure(0, weight=1)
        self.contenedor.rowconfigure(0, weight=1)
        self.paginas = []
        self._panel()
        self.camiones = self._crud('Camiones', 'camiones', [('camion_id', 'Camión'), ('placa', 'Placa'), ('empresa', 'Empresa'), ('certificacion_hasta', 'Vigencia')], formularios.camion)
        self.accesos = self._crud('Control de acceso', 'accesos', [('creado_en', 'Fecha UTC'), ('camion_id', 'Camión'), ('resultado', 'Resultado'), ('A', 'A'), ('E', 'E')], formularios.acceso)
        self._tablas()
        self.incidentes = self._crud('Incidentes', 'incidentes', [('creado_en', 'Fecha UTC'), ('categoria', 'Categoría'), ('prioridad', 'Prioridad'), ('estado', 'Estado'), ('revision', 'Revisión humana')], formularios.incidente,
            lambda d: [d['creado_en'], d['clasificacion']['categoria'], d['clasificacion']['prioridad'], d['estado'], d['requiere_revision_humana']])
        ttk.Button(self.incidentes.barra, text='Notificar soporte', command=self._notificar).pack(side='left')
        self._chat()
        self.riesgos = self._crud('Riesgos éticos', 'riesgos_eticos', [('modulo', 'Módulo'), ('categoria', 'Categoría'), ('puntaje_inicial', 'Antes'), ('puntaje_residual', 'Residual')], formularios.riesgo)
        self.riesgos.tabla.tree.configure(height=7)
        self.figura_riesgos = Figure(figsize=(7, 2.5), dpi=90, layout='constrained')
        self.canvas_riesgos = FigureCanvasTkAgg(self.figura_riesgos, master=self.riesgos)
        self.canvas_riesgos.get_tk_widget().pack(fill='both', expand=True)
        self.riesgos.al_actualizar = self._graficar_riesgos
        self.evaluaciones = self._crud('Evaluaciones LLM', 'evaluaciones_llm', [('creado_en', 'Fecha UTC'), ('tipo', 'Tipo'), ('modelo', 'Modelo'), ('latencia_ms', 'Latencia ms'), ('estado', 'Estado')], formularios.evaluacion)
        self._experimento()
        self._reportes()
        self._configuracion()
        self.menu.bind('<<ListboxSelect>>', self._cambiar_pagina)
        self.menu.selection_set(0)
        self.paginas[0].tkraise()
        self.root.protocol('WM_DELETE_WINDOW', self._cerrar)
        self.root.after(150, lambda: self.trabajos.ejecutar('Comprobando almacenamiento…', servicio.repo.comprobar, lambda texto: self.estado.set(texto)))

    def _pagina(self, nombre):
        pagina = ttk.Frame(self.contenedor, padding=16)
        self._agregar_pagina(nombre, pagina)
        ttk.Label(pagina, text=nombre, font=('TkDefaultFont', 17, 'bold')).pack(anchor='w', pady=(0, 12))
        return pagina

    def _agregar_pagina(self, nombre, pagina):
        self.menu.insert('end', nombre)
        self.paginas.append(pagina)
        pagina.grid(row=0, column=0, sticky='nsew')

    def _crud(self, nombre, coleccion, columnas, formulario, valores=None):
        pagina = PaginaCRUD(self, self.contenedor, nombre, coleccion, columnas,
                            lambda p, a: formulario(self, p, a), valores)
        self._agregar_pagina(nombre, pagina)
        return pagina

    def _cambiar_pagina(self, _=None):
        if self.menu.curselection():
            self.paginas[self.menu.curselection()[0]].tkraise()

    def _panel(self):
        pagina = self._pagina('Panel de control')
        barra = ttk.Frame(pagina)
        barra.pack(fill='x', pady=6)
        desde, hasta = tk.StringVar(), tk.StringVar()
        for titulo, var in [('Desde (AAAA-MM-DD)', desde), ('Hasta (AAAA-MM-DD)', hasta)]:
            ttk.Label(barra, text=titulo).pack(side='left', padx=(0, 6))
            ttk.Entry(barra, textvariable=var, width=13).pack(side='left', padx=(0, 12))
        resumen = tk.StringVar(value='Selecciona fechas o deja ambos campos vacíos para ver todos los registros.')
        ttk.Label(pagina, textvariable=resumen, font=('TkDefaultFont', 12), wraplength=850).pack(anchor='w', pady=15)
        figura = Figure(figsize=(8, 3), dpi=100, layout='constrained')
        canvas = FigureCanvasTkAgg(figura, master=pagina)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        tabla = Tabla(pagina, [('anio', 'Año ISO'), ('semana', 'Semana ISO'), ('categoria', 'Categoría'), ('total', 'Incidentes')], 5)
        tabla.pack(fill='both', expand=True)
        def mostrar(datos):
            resumen.set(f"Camiones atendidos: {datos['camiones_atendidos']}   |   Accesos: {datos['accesos']}\n"
                        f"Incidentes abiertos: {datos['incidentes_abiertos']}   |   Riesgos residuales críticos: {datos['riesgos_criticos']}")
            filas = datos['por_semana']
            tabla.mostrar(filas)
            figura.clear()
            eje = figura.add_subplot(111)
            if filas:
                eje.barh([f"{d['anio']}-S{d['semana']:02d} · {d['categoria']}" for d in filas], [d['total'] for d in filas], color='#2563eb')
                eje.set_xlabel('Número de incidentes')
            else:
                eje.text(.5, .5, 'Sin incidentes en el período', ha='center', va='center', transform=eje.transAxes)
            eje.set_title('Incidentes por categoría y semana (UTC)')
            canvas.draw_idle()
        def actualizar():
            d, h = desde.get(), hasta.get()
            self.trabajos.ejecutar('Actualizando indicadores y agregación…', lambda: self.servicio.panel(d, h), mostrar)
        ttk.Button(barra, text='Consultar', command=actualizar).pack(side='left')
        ttk.Label(pagina, text='El período filtra la fecha de creación; los indicadores muestran el estado actual de esos registros.').pack(anchor='w', pady=8)

    def _tablas(self):
        pagina = self._pagina('Tablas de verdad')
        fila = ttk.Frame(pagina)
        fila.pack(fill='x')
        variables = {k: tk.BooleanVar(value=False) for k in 'PQRSTH'}
        variables['H'].set(True)
        resultado = tk.StringVar()
        def actualizar():
            r = decidir(Premisas(**{k: v.get() for k, v in variables.items()}))
            resultado.set(f"A={r['A']}   E={r['E']}   B={r['B']}   F={r['F']}\nDecisión operativa: {r['resultado']}\n" + '\n'.join(r['explicacion']))
        for k, descripcion in [('P', 'Autorización'), ('Q', 'Sobrepeso'), ('R', 'Peligrosos'), ('S', 'Certificación'), ('H', 'Horario'), ('T', 'Fatiga')]:
            ttk.Checkbutton(fila, text=f'{k}: {descripcion}', variable=variables[k], command=actualizar).pack(side='left', padx=4)
        ttk.Label(pagina, textvariable=resultado, justify='left').pack(anchor='w', pady=12)
        notebook = ttk.Notebook(pagina)
        notebook.pack(fill='both', expand=True)
        for titulo, registros in tablas().items():
            tabla = Tabla(notebook, [(k, k) for k in registros[0]], 8)
            tabla.mostrar(registros, lambda d: ['V' if v else 'F' for v in d.values()])
            notebook.add(tabla, text=titulo)
        ttk.Label(pagina, text='A y E pueden ser verdaderas a la vez: la política da prioridad a inspección. El simulador no guarda accesos.').pack(anchor='w', pady=8)
        actualizar()

    def _chat(self):
        pagina = self._pagina('Asistente con fuentes')
        ttk.Label(pagina, text='Ejemplo: ¿por qué CAM-102 fue enviado a inspección? Cada respuesta cita registros recuperados.').pack(anchor='w')
        chat = ScrolledText(pagina, wrap='word', state='disabled', height=20)
        chat.pack(fill='both', expand=True, pady=10)
        pregunta = tk.StringVar()
        ttk.Entry(pagina, textvariable=pregunta).pack(fill='x', pady=6)
        barra = ttk.Frame(pagina)
        barra.pack(fill='x')
        def escribir(texto):
            chat.configure(state='normal')
            chat.insert('end', texto + '\n\n')
            chat.configure(state='disabled')
            chat.see('end')
        def consultar():
            texto = pregunta.get()
            cliente = self.servicio.clasificador.cliente
            usar_llm, operador = self.config.usar_llm, self.config.operador
            def listo(registro):
                escribir(f"Tú: {texto}\n\nAsistente ({registro['estado']}): {registro['respuesta_mostrada']}")
                if pregunta.get() == texto: pregunta.set('')
            self.trabajos.ejecutar('Recuperando registros y consultando fuentes…',
                lambda: responder(self.servicio.repo, cliente, texto, operador, usar_llm), listo)
        def historial():
            def mostrar(datos):
                chat.configure(state='normal'); chat.delete('1.0', 'end'); chat.configure(state='disabled')
                for d in reversed(datos):
                    escribir(f"Tú: {d.get('pregunta', '')}\nAsistente: {d.get('respuesta_mostrada', '')}")
            self.trabajos.ejecutar('Cargando historial…', lambda: self.servicio.repo.listar('evaluaciones_llm', {'tipo': 'asistente'}), mostrar)
        ttk.Button(barra, text='Preguntar', command=consultar).pack(side='left')
        ttk.Button(barra, text='Cargar historial', command=historial).pack(side='left', padx=8)

    def _graficar_riesgos(self, datos):
        self.figura_riesgos.clear()
        eje = self.figura_riesgos.add_subplot(111)
        ordenados = sorted(datos, key=lambda d: d['puntaje_residual'], reverse=True)
        if ordenados:
            posiciones = list(range(len(ordenados)))
            eje.bar([i - .18 for i in posiciones], [d['puntaje_inicial'] for d in ordenados], width=.36, label='Antes', color='#dc2626')
            eje.bar([i + .18 for i in posiciones], [d['puntaje_residual'] for d in ordenados], width=.36, label='Residual', color='#2563eb')
            eje.set_xticks(posiciones, [f"{i+1}. {d['modulo'][:17]}" for i, d in enumerate(ordenados)], rotation=20, ha='right')
            eje.axhline(self.config.umbral_riesgo, color='#92400e', linestyle='--', label='Umbral crítico')
            eje.legend()
        else:
            eje.text(.5, .5, 'Sin riesgos registrados', ha='center', va='center', transform=eje.transAxes)
        eje.set_ylim(0, 26)
        eje.set_ylabel('Probabilidad × impacto')
        eje.set_title('Riesgo inicial y residual (valoración estimada)')
        self.canvas_riesgos.draw_idle()

    def _notificar(self):
        if self.trabajos.ocupado: return
        try:
            d = self.incidentes.tabla.seleccionado()
        except ValueError as error:
            messagebox.showinfo('Selecciona un incidente', str(error), parent=self.root); return
        simulacion = self.config.simulacion_correo
        mensaje = '¿Preparar una notificación simulada?' if simulacion else '¿Enviar este resumen al destinatario SMTP_TO configurado en .env?'
        if messagebox.askyesno('Notificación a soporte', mensaje, default='no', parent=self.root):
            self.trabajos.ejecutar('Procesando notificación…', lambda: notificar(d, simulacion),
                                   lambda texto: messagebox.showinfo('Notificación', texto, parent=self.root))

    def _experimento(self):
        from logismart.servicios.evaluacion import evaluar_corpus, cargar_corpus
        pagina = self._pagina('Experimento')
        corpus_path = tk.StringVar(value=str(RAIZ / 'datos/correos_etiquetados.json'))
        ttk.Label(pagina, text='Conjunto sintético con etiquetas propuestas. Revisa y confirma manualmente cada correo antes de tu evaluación final.', wraplength=870).pack(anchor='w')
        ttk.Entry(pagina, textvariable=corpus_path).pack(fill='x', pady=8)
        barra = ttk.Frame(pagina); barra.pack(fill='x')
        salida = ScrolledText(pagina, height=20, wrap='word', state='disabled')
        salida.pack(fill='both', expand=True, pady=10)
        self.ultimo_experimento = None
        def mostrar(datos):
            self.ultimo_experimento = datos
            salida.configure(state='normal'); salida.delete('1.0', 'end')
            salida.insert('end', json.dumps({k: v for k, v in datos.items() if k != 'casos'}, ensure_ascii=False, indent=2))
            salida.configure(state='disabled')
        def ejecutar():
            ruta = Path(corpus_path.get())
            motor, repo, operador = self.servicio.clasificador, self.servicio.repo, self.config.operador
            self.trabajos.ejecutar('Evaluando corpus (puede tardar varios minutos)…', lambda: evaluar_corpus(ruta, motor, repo, operador), mostrar)
        def exportar_resultado():
            if self.ultimo_experimento is None:
                messagebox.showinfo('Evaluación', 'Ejecuta primero el experimento.', parent=self.root); return
            ruta = filedialog.asksaveasfilename(parent=self.root, defaultextension='.json', filetypes=[('JSON', '*.json'), ('PDF', '*.pdf')])
            if ruta:
                datos = self.ultimo_experimento
                self.trabajos.ejecutar('Exportando resultados…', lambda: exportar(datos, ruta, 'Experimento de clasificación'), lambda r: self.estado.set(f'Guardado: {r}'))
        def revisar():
            try:
                registros = cargar_corpus(Path(corpus_path.get()))
            except (ValueError, OSError) as error:
                messagebox.showerror('Corpus', str(error), parent=self.root); return
            from logismart.presentacion.revision_corpus import abrir_revision
            abrir_revision(self, registros, corpus_path)
        ttk.Button(barra, text='Revisar etiquetas manualmente', command=revisar).pack(side='left')
        ttk.Button(barra, text='Ejecutar comparación', command=ejecutar).pack(side='left', padx=8)
        ttk.Button(barra, text='Exportar resultados', command=exportar_resultado).pack(side='left')

    def _reportes(self):
        pagina = self._pagina('Reportes')
        coleccion = tk.StringVar(value='accesos')
        desde, hasta = tk.StringVar(), tk.StringVar()
        for etiqueta, var in [('Colección', coleccion), ('Desde (AAAA-MM-DD, UTC)', desde), ('Hasta (AAAA-MM-DD, UTC)', hasta)]:
            ttk.Label(pagina, text=etiqueta).pack(anchor='w', pady=(8, 2))
            widget = ttk.Combobox(pagina, textvariable=var, values=COLECCIONES, state='readonly') if var is coleccion else ttk.Entry(pagina, textvariable=var)
            widget.pack(fill='x')
        ttk.Label(pagina, text='La exportación incluye los registros activos del período y su historial. Los correos y prompts pueden contener datos personales.', wraplength=850).pack(anchor='w', pady=15)
        def guardar():
            ruta = filedialog.asksaveasfilename(parent=self.root, defaultextension='.pdf', filetypes=[('PDF', '*.pdf'), ('CSV', '*.csv'), ('JSON', '*.json')])
            if not ruta: return
            c, d, h = coleccion.get(), desde.get(), hasta.get()
            self.trabajos.ejecutar('Consultando y exportando…', lambda: exportar(self.servicio.repo.listar(c, desde=d, hasta=h), ruta, f'LogiSmart · {c}'), lambda r: self.estado.set(f'Exportado: {r}'))
        ttk.Button(pagina, text='Exportar PDF / CSV / JSON', command=guardar).pack(anchor='w')

    def _configuracion(self):
        pagina = self._pagina('Configuración')
        informacion = tk.StringVar()
        def actualizar_info():
            informacion.set(f'Modelo: {self.config.modelo}\nLLM habilitado: {self.config.usar_llm}\nOperador: {self.config.operador}\n'
                            f'Horario de peligrosos: {self.config.hora_inicio}:00 a {self.config.hora_fin}:00 (México)\n'
                            f'Umbral de riesgo residual: {self.config.umbral_riesgo}\nSimulación de correo: {self.config.simulacion_correo}')
        ttk.Label(pagina, textvariable=informacion, font=('TkDefaultFont', 12), justify='left').pack(anchor='w', pady=10)
        def editar():
            if self.trabajos.ocupado: return
            campos = [('modelo', 'Modelo instalado en Ollama', 'cadena', None), ('url_ollama', 'Servidor local de Ollama', 'cadena', None),
                      ('timeout', 'Espera máxima por llamada (5–300 s)', 'entero', None), ('usar_llm', 'Habilitar LLM real', 'bool', None),
                      ('operador', 'Operador (2–80 caracteres)', 'cadena', None), ('umbral_riesgo', 'Umbral crítico (1–25)', 'entero', None),
                      ('hora_inicio', 'Hora inicial (0–23)', 'entero', None), ('hora_fin', 'Hora final exclusiva (1–24)', 'entero', None),
                      ('simulacion_correo', 'Simular correo (sin envío real)', 'bool', None)]
            def guardar(f, d):
                config = validar(Configuracion, d)
                cliente = OllamaLocal(config.modelo, config.url_ollama, config.timeout)
                guardar_configuracion(config)
                self.config = self.servicio.config = config
                self.servicio.clasificador = ClasificadorHibrido(cliente, config.usar_llm)
                f.destroy(); actualizar_info()
            Formulario(self, 'Configuración operativa', campos, self.config.model_dump(), guardar)
        ttk.Button(pagina, text='Editar configuración', command=editar).pack(anchor='w', pady=8)
        ttk.Button(pagina, text='Comprobar conexión a almacenamiento', command=lambda: self.trabajos.ejecutar('Comprobando…', self.servicio.repo.comprobar, lambda r: messagebox.showinfo('Conexión', r, parent=self.root))).pack(anchor='w', pady=8)
        def cargar_demo():
            if self.trabajos.ocupado: return
            if messagebox.askyesno('Datos ficticios', f'¿Agregar datos de demostración a {self.servicio.repo.modo}?\nNo se reemplazarán registros existentes.', default='no', parent=self.root):
                from logismart.servicios.demostracion import cargar_demo
                self.trabajos.ejecutar('Cargando demostración…', lambda: cargar_demo(self.servicio), lambda r: messagebox.showinfo('Demostración', r, parent=self.root))
        ttk.Button(pagina, text='Cargar datos de demostración', command=cargar_demo).pack(anchor='w', pady=8)
        ttk.Label(pagina, text='Las credenciales de MongoDB y SMTP se configuran únicamente en .env. Reinicia la aplicación después de cambiarlas. Las preferencias de esta pantalla se guardan localmente.', wraplength=820).pack(anchor='w', pady=15)
        actualizar_info()

    def _cerrar(self):
        if self.trabajos.puede_cerrar():
            self.servicio.repo.cerrar()
            self.root.destroy()

    def ejecutar(self):
        self.root.mainloop()
