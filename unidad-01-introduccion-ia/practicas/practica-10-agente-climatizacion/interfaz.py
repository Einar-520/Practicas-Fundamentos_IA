"""Interfaz Tkinter: percibir y decidir en pantalla; registrar en segundo plano."""

import json
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from agente_climatizacion import ACCIONES, AgenteClimatizacion
from graficas import dibujar_graficas, fecha_utc
from almacenamiento_atlas import AlmacenamientoAtlas, ErrorAtlas


TODAS = 'Todas las acciones'
REGLAS = dict(zip(ACCIONES, (
    'Temperatura mayor de 30 °C y humedad mayor de 70 %.',
    'Temperatura mayor de 30 °C y humedad menor o igual a 70 %.',
    'Temperatura menor de 18 °C.',
    'Temperatura entre 18 y 30 °C, incluidos ambos límites.',
)))


def trabajar(almacenamiento, operacion, agente, resultados, identificador=None, pagina=0, accion=None):
    """Confirmar la escritura y consultar la tabla en pasos separados, sin tocar widgets."""
    respuesta = {'ok': False, 'confirmado': False, 'identificador': identificador}
    try:
        if operacion == 'crear':
            documento = agente.ejecutar(almacenamiento)
            respuesta.update(confirmado=True, identificador=documento['_id'],
                             mensaje='Registro creado y confirmado por Atlas.')
            pagina = 0
        elif operacion == 'actualizar':
            agente.ejecutar(almacenamiento, identificador)
            respuesta.update(confirmado=True, mensaje='Cambios guardados y confirmados por Atlas.')
        elif operacion == 'eliminar':
            almacenamiento.eliminar(identificador)
            respuesta.update(confirmado=True, mensaje='Registro eliminado y confirmado por Atlas.')
        elif operacion != 'listar':
            raise ValueError('Operación desconocida.')
        if respuesta['confirmado'] and agente is not None and accion not in (None, agente.accion):
            respuesta['mensaje'] += f' Para verlo selecciona «{agente.accion}» o Todas las acciones.'
        listado = almacenamiento.listar(pagina, accion)
        if not listado['registros'] and pagina > 0:
            listado = almacenamiento.listar(pagina - 1, accion)
        respuesta.update(ok=True, listado=listado)
        if operacion == 'listar':
            respuesta['mensaje'] = 'Lista consultada en Atlas. Selecciona un registro para editarlo.'
    except (ErrorAtlas, ValueError) as error:
        if respuesta['confirmado']:
            respuesta['mensaje'] += ' No se pudo refrescar la lista. Pulsa Actualizar lista.'
        else:
            respuesta['mensaje'] = str(error)
    except Exception:
        if respuesta['confirmado']:
            respuesta['mensaje'] += ' No se pudo refrescar la lista. Pulsa Actualizar lista.'
        else:
            respuesta['mensaje'] = 'No se pudo completar la operación. Actualiza la lista antes de reintentar.'
    resultados.put({**respuesta, 'operacion': operacion,
                    'base': almacenamiento.base, 'coleccion': almacenamiento.coleccion})


class VentanaClimatizacion:
    def __init__(self, ventana, almacenamiento=None):
        self.ventana = ventana
        self.almacenamiento = almacenamiento if almacenamiento is not None else AlmacenamientoAtlas()
        self.resultados = Queue()
        self.ocupado = self.cerrando = self.cerrada = False
        self.sondeo = None
        self.registros = {}
        self.seleccionado = None
        self.pagina = 0
        self.hay_siguiente = False
        self.lista_vigente = False
        self.renderizando = False
        self.pendiente_seleccion = None
        self.ventana.title('Práctica 10 · Agente de climatización')
        self.ventana.geometry('1200x860')
        self.ventana.minsize(1040, 780)
        self.ventana.configure(background='#eef3f7')
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(1, weight=1)
        self._crear_interfaz()
        self.ventana.protocol('WM_DELETE_WINDOW', self.cerrar)
        self.ventana.bind('<Control-Return>', lambda evento: self.guardar_desde_teclado())
        self.ventana.bind('<Configure>', self._ajustar)
        self.temperatura.trace_add('write', self._lectura_modificada)
        self.humedad.trace_add('write', self._lectura_modificada)
        self.entrada_temperatura.focus_set()
        self.consultar()

    def _crear_interfaz(self):
        estilo = ttk.Style(self.ventana)
        if 'clam' in estilo.theme_names():
            estilo.theme_use('clam')
        estilo.configure('TFrame', background='#eef3f7')
        estilo.configure('Tarjeta.TFrame', background='#ffffff')
        estilo.configure('TLabel', background='#eef3f7', foreground='#183447', font=('TkDefaultFont', 10))
        estilo.configure('Titulo.TLabel', font=('TkDefaultFont', 22, 'bold'))
        estilo.configure('Tarjeta.TLabel', background='#ffffff')
        estilo.configure('Subtitulo.TLabel', background='#ffffff', font=('TkDefaultFont', 12, 'bold'))
        estilo.configure('Accion.TLabel', background='#ffffff', foreground='#176346', font=('TkDefaultFont', 10, 'bold'))
        estilo.configure('TButton', padding=(10, 6), font=('TkDefaultFont', 10))
        estilo.configure('Guardar.TButton', background='#176346', foreground='#ffffff')
        estilo.map('Guardar.TButton', background=[('disabled', '#dce6df'), ('active', '#104b34')],
                   foreground=[('disabled', '#52665a')])
        estilo.configure('TEntry', padding=6)

        cabecera = ttk.Frame(self.ventana, padding=(18, 12))
        cabecera.grid(row=0, column=0, sticky='ew')
        ttk.Label(cabecera, text='PRÁCTICA 10 · FUNDAMENTOS DE IA · Einar Ivan Lazcano Luna').pack(anchor='w')
        ttk.Label(cabecera, text='Agente de climatización', style='Titulo.TLabel').pack(anchor='w')
        self.destino = tk.StringVar(value='Conexión: configuración local del .env de la práctica 10.')
        self.etiqueta_destino = ttk.Label(cabecera, textvariable=self.destino, wraplength=1080)
        self.etiqueta_destino.pack(anchor='w', pady=(4, 0))

        cuerpo = ttk.Frame(self.ventana, padding=(18, 0))
        cuerpo.grid(row=1, column=0, sticky='nsew')
        cuerpo.rowconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=1)
        lateral = ttk.Frame(cuerpo, padding=14, style='Tarjeta.TFrame', width=280)
        lateral.grid(row=0, column=0, sticky='ns', padx=(0, 12))
        principal = ttk.Frame(cuerpo)
        principal.grid(row=0, column=1, sticky='nsew')
        principal.columnconfigure(0, weight=1)
        principal.rowconfigure(1, weight=3, minsize=195)
        principal.rowconfigure(2, weight=4, minsize=270)

        filtro = ttk.Frame(principal, padding=12, style='Tarjeta.TFrame')
        filtro.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        filtro.columnconfigure(0, weight=1)
        ttk.Label(filtro, text='¿Qué acción quieres consultar?', style='Subtitulo.TLabel').grid(row=0, column=0, sticky='w')
        self.filtro_accion = tk.StringVar(value=TODAS)
        self.selector_accion = ttk.Combobox(filtro, textvariable=self.filtro_accion,
                                           values=(TODAS, *ACCIONES), state='readonly', width=40)
        self.selector_accion.grid(row=1, column=0, sticky='ew', pady=(6, 4))
        self.selector_accion.bind('<<ComboboxSelected>>', self.cambiar_accion)
        self.boton_consultar = ttk.Button(filtro, text='Actualizar lista', command=self.consultar)
        self.boton_consultar.grid(row=1, column=1, padx=(8, 0))
        self.regla = tk.StringVar(value='Todas las acciones de tus registros de la práctica 10.')
        self.etiqueta_regla = ttk.Label(filtro, textvariable=self.regla, style='Tarjeta.TLabel', wraplength=650)
        self.etiqueta_regla.grid(row=2, column=0, columnspan=2, sticky='w')

        ttk.Label(lateral, text='Gestionar registros', style='Subtitulo.TLabel').pack(anchor='w', pady=(0, 12))
        self.temperatura, self.humedad = tk.StringVar(), tk.StringVar()
        ttk.Label(lateral, text='Temperatura (°C)', style='Tarjeta.TLabel').pack(anchor='w')
        self.entrada_temperatura = ttk.Entry(lateral, textvariable=self.temperatura, width=26)
        self.entrada_temperatura.pack(fill='x', pady=(4, 10))
        ttk.Label(lateral, text='Humedad (%) · de 0 a 100', style='Tarjeta.TLabel').pack(anchor='w')
        self.entrada_humedad = ttk.Entry(lateral, textvariable=self.humedad, width=26)
        self.entrada_humedad.pack(fill='x', pady=(4, 6))
        ttk.Label(lateral, text='Admite punto o coma decimal.', style='Tarjeta.TLabel').pack(anchor='w', pady=(0, 12))
        self.boton_guardar = ttk.Button(lateral, text='Crear registro', command=self.evaluar_y_guardar, style='Guardar.TButton')
        self.boton_actualizar = ttk.Button(lateral, text='Guardar cambios', command=self.guardar_cambios)
        self.boton_eliminar = ttk.Button(lateral, text='Eliminar seleccionado', command=self.eliminar_seleccionado)
        self.boton_limpiar = ttk.Button(lateral, text='Nuevo / limpiar', command=self.limpiar)
        self.botones = (self.boton_guardar, self.boton_actualizar, self.boton_eliminar,
                        self.boton_limpiar, self.boton_consultar)
        for boton in self.botones[:-1]:
            boton.pack(fill='x', pady=(0, 6))
        self.entradas = (self.entrada_temperatura, self.entrada_humedad)
        self.modo = tk.StringVar(value='Nuevo registro')
        ttk.Label(lateral, textvariable=self.modo, style='Tarjeta.TLabel', wraplength=245).pack(anchor='w', pady=(6, 8))
        self.resumen = tk.StringVar(value='Ingresa una lectura para conocer la acción del agente.')
        self.etiqueta_resumen = ttk.Label(lateral, textvariable=self.resumen, style='Accion.TLabel', wraplength=245)
        self.etiqueta_resumen.pack(anchor='w', pady=(0, 12))
        ttk.Label(lateral, text='Detalle del seleccionado', style='Tarjeta.TLabel').pack(anchor='w')
        self.documento = ScrolledText(lateral, width=28, height=5, wrap='word',
                                     font=('TkFixedFont', 9), relief='solid', borderwidth=1,
                                     background='#f6f9fb', foreground='#183447', padx=6, pady=6)
        self.documento.pack(fill='both', expand=True, pady=(4, 0))
        self._mostrar_documento(None)

        consulta = ttk.Frame(principal, padding=12, style='Tarjeta.TFrame')
        consulta.grid(row=1, column=0, sticky='nsew', pady=(0, 10))
        consulta.columnconfigure(0, weight=1)
        consulta.rowconfigure(1, weight=1)
        self.vigencia = tk.StringVar(value='Registros en Atlas · cargando…')
        ttk.Label(consulta, textvariable=self.vigencia, style='Subtitulo.TLabel').grid(row=0, column=0, sticky='w', pady=(0, 6))
        marco_tabla = ttk.Frame(consulta)
        marco_tabla.grid(row=1, column=0, sticky='nsew')
        marco_tabla.columnconfigure(0, weight=1)
        marco_tabla.rowconfigure(0, weight=1)
        columnas = ('fecha', 'temperatura', 'humedad', 'accion')
        self.tabla = ttk.Treeview(marco_tabla, columns=columnas, show='headings', selectmode='browse', height=5)
        for nombre, titulo, ancho in [('fecha', 'Fecha (UTC)', 155), ('temperatura', 'Temp. °C', 80),
                                      ('humedad', 'Humedad %', 85), ('accion', 'Acción del agente', 370)]:
            self.tabla.heading(nombre, text=titulo)
            self.tabla.column(nombre, width=ancho, minwidth=60, stretch=nombre == 'accion')
        vertical = ttk.Scrollbar(marco_tabla, orient='vertical', command=self.tabla.yview)
        horizontal = ttk.Scrollbar(marco_tabla, orient='horizontal', command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.grid(row=0, column=0, sticky='nsew')
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        self.tabla.bind('<<TreeviewSelect>>', self.seleccionar_registro)
        paginas = ttk.Frame(consulta, style='Tarjeta.TFrame')
        paginas.grid(row=2, column=0, sticky='ew', pady=(6, 0))
        self.boton_anterior = ttk.Button(paginas, text='Anterior', command=lambda: self.cambiar_pagina(-1))
        self.boton_siguiente = ttk.Button(paginas, text='Siguiente', command=lambda: self.cambiar_pagina(1))
        self.paginacion = tk.StringVar(value='Página 1')
        self.boton_anterior.pack(side='left')
        ttk.Label(paginas, textvariable=self.paginacion, style='Tarjeta.TLabel').pack(side='left', padx=10)
        self.boton_siguiente.pack(side='left')

        graficas = ttk.Frame(principal, padding=(12, 10), style='Tarjeta.TFrame')
        graficas.grid(row=2, column=0, sticky='nsew')
        graficas.columnconfigure(0, weight=1)
        graficas.rowconfigure(2, weight=1)
        ttk.Label(graficas, text='Gráficas de los registros de esta página', style='Subtitulo.TLabel').grid(row=0, column=0, sticky='w')
        self.resumen_graficas = tk.StringVar()
        self.etiqueta_graficas = ttk.Label(graficas, textvariable=self.resumen_graficas, style='Tarjeta.TLabel', wraplength=680)
        self.etiqueta_graficas.grid(row=1, column=0, sticky='w', pady=(4, 0))
        self.figura = Figure(figsize=(7.4, 2.6), dpi=90, layout='constrained', facecolor='#ffffff')
        self.lienzo = FigureCanvasTkAgg(self.figura, master=graficas)
        self.lienzo.get_tk_widget().grid(row=2, column=0, sticky='nsew')
        self._actualizar_graficas([], 'Esperando la consulta de Atlas')

        pie = ttk.Frame(self.ventana, padding=(18, 8, 18, 12))
        pie.grid(row=2, column=0, sticky='ew')
        pie.columnconfigure(0, weight=1)
        self.progreso = ttk.Progressbar(pie, mode='indeterminate')
        self.progreso.grid(row=0, column=0, sticky='ew', pady=(0, 6))
        self.estado = tk.StringVar(value='Consultando tus registros en Atlas…')
        self.etiqueta_estado = ttk.Label(pie, textvariable=self.estado, wraplength=1100)
        self.etiqueta_estado.grid(row=1, column=0, sticky='w')

    def _ajustar(self, evento):
        if evento.widget is self.ventana:
            for etiqueta in (self.etiqueta_destino, self.etiqueta_estado):
                etiqueta.configure(wraplength=max(300, evento.width - 48))
            for etiqueta in (self.etiqueta_regla, self.etiqueta_graficas):
                etiqueta.configure(wraplength=max(400, evento.width - 370))

    def _actualizar_graficas(self, registros, mensaje_vacio='Sin registros para esta consulta'):
        self.resumen_graficas.set(dibujar_graficas(self.figura, registros, mensaje_vacio))
        self.lienzo.draw_idle()

    def _vaciar_resultados(self, mensaje):
        self.registros = {}
        filas = self.tabla.get_children()
        if filas:
            self.tabla.delete(*filas)
        self._mostrar_documento(None)
        self._actualizar_graficas([], mensaje)
        self.vigencia.set(mensaje)
        self.lista_vigente = False

    def cambiar_accion(self, evento=None):
        if not self._disponible():
            return
        self.pagina = 0
        self._nuevo_formulario()
        self.regla.set(REGLAS.get(self.filtro_accion.get(), 'Todas las acciones de tus registros de la práctica 10.'))
        self._vaciar_resultados('Consultando la acción seleccionada…')
        self.consultar()

    def _mensaje(self, mensaje, error=False):
        self.estado.set(mensaje)
        self.etiqueta_estado.configure(foreground='#a32828' if error else '#183447')

    def _lectura_modificada(self, *_):
        if not self.ocupado and not self.renderizando:
            self.resumen.set('Lectura modificada. Al guardar, el agente recalculará la acción.')

    def _disponible(self):
        return not (self.ocupado or self.cerrando or self.cerrada)

    def _calcular_agente(self):
        agente = AgenteClimatizacion()
        try:
            agente.percibir(self.temperatura.get(), self.humedad.get())
            agente.tomar_decision()
        except ValueError as error:
            self._mensaje(str(error), error=True)
            entrada = self.entrada_humedad if 'humedad' in str(error) else self.entrada_temperatura
            entrada.focus_set()
            return None
        self.resumen.set(agente.mostrar_resultado())
        return agente

    def guardar_desde_teclado(self):
        if self.seleccionado is None:
            self.evaluar_y_guardar()
        else:
            self.guardar_cambios()

    def evaluar_y_guardar(self):
        if not self._disponible() or not self.lista_vigente:
            return
        if self.seleccionado is not None:
            self._mensaje('Pulsa Nuevo / limpiar para crear otro registro.', error=True)
            return
        agente = self._calcular_agente()
        if agente is not None:
            self._enviar('crear', agente)

    def guardar_cambios(self):
        if not self._disponible() or not self.lista_vigente:
            return
        if self.seleccionado not in self.registros:
            self._mensaje('Selecciona primero el registro que quieres modificar.', error=True)
            return
        agente = self._calcular_agente()
        if agente is not None:
            self._enviar('actualizar', agente, self.seleccionado)

    def eliminar_seleccionado(self):
        if not self._disponible() or not self.lista_vigente:
            return
        identificador = self.seleccionado
        if identificador not in self.registros:
            self._mensaje('Selecciona primero el registro que quieres eliminar.', error=True)
            return
        registro = self.registros[identificador]
        mensaje = (f'Registro: {identificador}\n'
                   f'Temperatura: {registro["temperatura"]} °C · Humedad: {registro["humedad"]} %\n\n'
                   '¿Eliminar este registro del clúster del profesor?')
        if messagebox.askyesno('Confirmar eliminación', mensaje, parent=self.ventana,
                              icon='warning', default='no'):
            self._enviar('eliminar', identificador=identificador)

    def consultar(self):
        self._enviar('listar', pagina=self.pagina)

    def cambiar_pagina(self, cambio):
        if not self._disponible() or not self.lista_vigente:
            return
        if cambio == -1 and self.pagina > 0:
            self._nuevo_formulario()
            self._enviar('listar', pagina=self.pagina - 1)
        elif cambio == 1 and self.hay_siguiente:
            self._nuevo_formulario()
            self._enviar('listar', pagina=self.pagina + 1)

    def limpiar(self):
        if not self._disponible():
            return
        self._nuevo_formulario()
        self._mensaje('Nuevo registro. Los registros guardados se conservan en Atlas.')
        self.entrada_temperatura.focus_set()
        self._habilitar_controles()

    def _nuevo_formulario(self):
        self.seleccionado = None
        self.pendiente_seleccion = None
        self.tabla.selection_remove(*self.tabla.selection())
        self.temperatura.set('')
        self.humedad.set('')
        self.modo.set('Nuevo registro')
        self.resumen.set('Ingresa una lectura para conocer la acción del agente.')
        self._mostrar_documento(None)

    def _mostrar_documento(self, documento):
        self.documento.configure(state='normal')
        self.documento.delete('1.0', 'end')
        texto = (json.dumps(documento, ensure_ascii=False, indent=2, default=str) if documento is not None
                 else 'Selecciona un registro de la tabla para ver sus datos completos.')
        self.documento.insert('1.0', texto)
        self.documento.configure(state='disabled')

    def seleccionar_registro(self, evento=None):
        if not self._disponible() or self.renderizando or not self.lista_vigente:
            return
        seleccion = self.tabla.selection()
        if not seleccion or seleccion[0] not in self.registros:
            return
        identificador = seleccion[0]
        if identificador == self.seleccionado:
            return  # Un refresco de la tabla no borra los cambios escritos en el formulario.
        self._cargar_registro(identificador)
        self._habilitar_controles()

    def _cargar_registro(self, identificador):
        registro = self.registros[identificador]
        self.seleccionado = identificador
        self.temperatura.set(str(registro['temperatura']))
        self.humedad.set(str(registro['humedad']))
        self.modo.set(f'Editando el registro: {identificador}')
        self.resumen.set(f'Acción guardada → {registro["accion"]}')
        self._mostrar_documento(registro)

    def _habilitar_controles(self):
        libre = self._disponible()
        for control in (*self.botones, *self.entradas, self.boton_anterior, self.boton_siguiente):
            control.state(['!disabled'] if libre else ['disabled'])
        edicion = self.seleccionado in self.registros
        for boton, habilitar in ((self.boton_guardar, libre and self.lista_vigente and not edicion),
                                 (self.boton_actualizar, libre and self.lista_vigente and edicion),
                                 (self.boton_eliminar, libre and self.lista_vigente and edicion),
                                 (self.boton_anterior, libre and self.lista_vigente and self.pagina > 0),
                                 (self.boton_siguiente, libre and self.lista_vigente and self.hay_siguiente)):
            boton.state(['!disabled'] if habilitar else ['disabled'])
        self.tabla.configure(selectmode='browse' if libre and self.lista_vigente else 'none')
        self.selector_accion.configure(state='readonly' if libre else 'disabled')

    def _enviar(self, operacion, agente=None, identificador=None, pagina=None):
        if not self._disponible():
            return
        self.ocupado = True
        self._habilitar_controles()
        self.progreso.start(12)
        mensajes = {'crear': 'Decisión calculada. Creando el registro en Atlas…',
                    'actualizar': 'Acción recalculada. Guardando los cambios en Atlas…',
                    'eliminar': 'Eliminando el registro seleccionado en Atlas…',
                    'listar': 'Consultando los registros en Atlas…'}
        self._mensaje(mensajes[operacion])
        Thread(target=trabajar, args=(self.almacenamiento, operacion, agente, self.resultados,
                                     identificador, self.pagina if pagina is None else pagina,
                                     None if self.filtro_accion.get() == TODAS else self.filtro_accion.get()), daemon=True).start()
        self.sondeo = self.ventana.after(80, self._recibir)

    def _aplicar_listado(self, respuesta):
        listado = respuesta['listado']
        self.pagina, self.hay_siguiente = listado['pagina'], listado['hay_siguiente']
        self.registros = {d['_id']: d for d in listado['registros']}
        self.renderizando = True
        try:
            filas = self.tabla.get_children()
            if filas:
                self.tabla.delete(*filas)
            for identificador, d in self.registros.items():
                fecha = fecha_utc(d.get('fecha'))
                fecha = fecha.strftime('%Y-%m-%d %H:%M:%S') if fecha else 'Sin fecha válida'
                self.tabla.insert('', 'end', iid=identificador,
                                  values=(fecha, d['temperatura'], d['humedad'], d['accion']))
            elegido = self.pendiente_seleccion or self.seleccionado
            if elegido in self.registros:
                if self.pendiente_seleccion:
                    self._cargar_registro(elegido)
                else:
                    self._mostrar_documento(self.registros[elegido])
                self.tabla.selection_set(elegido)
                self.tabla.see(elegido)
            elif self.seleccionado is not None or self.pendiente_seleccion is not None:
                self._nuevo_formulario()
            self.pendiente_seleccion = None
        finally:
            self.renderizando = False
        self.paginacion.set(f'Página {self.pagina + 1} · {len(self.registros)} registros')
        self._actualizar_graficas(list(self.registros.values()))
        self.vigencia.set('Registros consultados en Atlas' if self.registros else 'Todavía no hay registros en esta página')

    def _recibir(self):
        self.sondeo = None
        try:
            respuesta = self.resultados.get_nowait()
        except Empty:
            self.sondeo = self.ventana.after(80, self._recibir)
            return
        self.progreso.stop()
        if respuesta['base'] and respuesta['coleccion']:
            self.destino.set(f"Base: {respuesta['base']} · Colección: {respuesta['coleccion']}")
        if respuesta['confirmado']:
            if respuesta['operacion'] == 'crear':
                self.pagina = 0
            if respuesta['operacion'] == 'eliminar':
                self._nuevo_formulario()
            else:
                self.pendiente_seleccion = respuesta['identificador']
        self.lista_vigente = respuesta['ok']
        if respuesta['ok']:
            self._aplicar_listado(respuesta)
        else:
            self._vaciar_resultados('Consulta pendiente; pulsa Actualizar lista')
        self._mensaje(respuesta['mensaje'], error=not respuesta['ok'])
        self.ocupado = False
        if self.cerrando:
            self.cerrar()
            return
        self._habilitar_controles()

    def cerrar(self):
        if self.cerrada:
            return
        self.cerrando = True
        if self.ocupado:
            self._mensaje('Esperando que termine la operación para cerrar la conexión…')
            return
        if self.sondeo is not None:
            self.ventana.after_cancel(self.sondeo)
        self.almacenamiento.cerrar()
        self.cerrada = True
        self.ventana.destroy()


def iniciar():
    try:
        ventana = tk.Tk()
    except tk.TclError:
        print('No se pudo abrir la ventana. Comprueba Tkinter y el soporte gráfico WSLg.')
        print('Prueba: python3 -m tkinter. Consulta el README de la práctica 10.')
        return 1
    app = VentanaClimatizacion(ventana)
    try:
        ventana.mainloop()
    finally:
        app.almacenamiento.cerrar()
    return 0
