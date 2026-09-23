"""Interfaz Tkinter: percibir y decidir en pantalla; registrar en segundo plano."""

import json
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from agente_climatizacion import AgenteClimatizacion
from almacenamiento_atlas import AlmacenamientoAtlas, ErrorAtlas


def trabajar(almacenamiento, operacion, agente, resultados, identificador=None, pagina=0):
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
        listado = almacenamiento.listar(pagina)
        if not listado['registros'] and pagina > 0:
            listado = almacenamiento.listar(pagina - 1)
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
        self.ventana.geometry('1000x720')
        self.ventana.minsize(860, 660)
        self.ventana.configure(background='#eef3f7')
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(3, weight=1)
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
        estilo.configure('Titulo.TLabel', font=('TkDefaultFont', 24, 'bold'))
        estilo.configure('Tarjeta.TLabel', background='#ffffff')
        estilo.configure('Subtitulo.TLabel', background='#ffffff', font=('TkDefaultFont', 12, 'bold'))
        estilo.configure('Accion.TLabel', background='#ffffff', foreground='#176346', font=('TkDefaultFont', 12, 'bold'))
        estilo.configure('TButton', padding=(12, 8), font=('TkDefaultFont', 10))
        estilo.configure('Guardar.TButton', background='#176346', foreground='#ffffff')
        estilo.map('Guardar.TButton', background=[('disabled', '#dce6df'), ('active', '#104b34')],
                   foreground=[('disabled', '#52665a')])
        estilo.configure('TEntry', padding=7, font=('TkDefaultFont', 12))

        cabecera = ttk.Frame(self.ventana, padding=(24, 18, 24, 12))
        cabecera.grid(row=0, column=0, sticky='ew')
        ttk.Label(cabecera, text='PRÁCTICA 10  /  FUNDAMENTOS DE IA').pack(anchor='w')
        ttk.Label(cabecera, text='Agente de climatización', style='Titulo.TLabel').pack(anchor='w', pady=(4, 5))
        ttk.Label(cabecera, text='Crear · consultar · actualizar · eliminar en Atlas · Einar Ivan Lazcano Luna').pack(anchor='w')
        self.destino = tk.StringVar(value='Conexión: configuración local del .env de la práctica 10.')
        self.etiqueta_destino = ttk.Label(cabecera, textvariable=self.destino, wraplength=780)
        self.etiqueta_destino.pack(anchor='w', pady=(8, 0))

        formulario = ttk.Frame(self.ventana, padding=16, style='Tarjeta.TFrame')
        formulario.grid(row=1, column=0, sticky='ew', padx=24)
        formulario.columnconfigure(0, weight=1, uniform='entrada')
        formulario.columnconfigure(1, weight=1, uniform='entrada')
        ttk.Label(formulario, text='Temperatura actual (°C)', style='Subtitulo.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(formulario, text='Humedad actual (%)', style='Subtitulo.TLabel').grid(row=0, column=1, sticky='w', padx=(14, 0))
        self.temperatura, self.humedad = tk.StringVar(), tk.StringVar()
        self.entrada_temperatura = ttk.Entry(formulario, textvariable=self.temperatura, width=18)
        self.entrada_humedad = ttk.Entry(formulario, textvariable=self.humedad, width=18)
        self.entrada_temperatura.grid(row=1, column=0, sticky='ew', pady=(8, 5))
        self.entrada_humedad.grid(row=1, column=1, sticky='ew', padx=(14, 0), pady=(8, 5))
        ttk.Label(formulario, text='Admite punto o coma decimal.', style='Tarjeta.TLabel').grid(row=2, column=0, sticky='w')
        ttk.Label(formulario, text='Valor entre 0 y 100.', style='Tarjeta.TLabel').grid(row=2, column=1, sticky='w', padx=(14, 0))
        botones = ttk.Frame(formulario, style='Tarjeta.TFrame')
        botones.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(14, 0))
        self.boton_guardar = ttk.Button(botones, text='Crear registro', command=self.evaluar_y_guardar, style='Guardar.TButton')
        self.boton_actualizar = ttk.Button(botones, text='Guardar cambios', command=self.guardar_cambios)
        self.boton_eliminar = ttk.Button(botones, text='Eliminar seleccionado', command=self.eliminar_seleccionado)
        self.boton_limpiar = ttk.Button(botones, text='Nuevo / limpiar', command=self.limpiar)
        self.boton_consultar = ttk.Button(botones, text='Actualizar lista', command=self.consultar)
        self.botones = (self.boton_guardar, self.boton_actualizar, self.boton_eliminar,
                        self.boton_limpiar, self.boton_consultar)
        for columna, boton in enumerate(self.botones):
            boton.grid(row=0, column=columna, padx=(0, 6), sticky='ew')
            botones.columnconfigure(columna, weight=1)
        self.entradas = (self.entrada_temperatura, self.entrada_humedad)
        self.modo = tk.StringVar(value='Nuevo registro')
        ttk.Label(formulario, textvariable=self.modo, style='Tarjeta.TLabel').grid(
            row=4, column=0, columnspan=2, sticky='w', pady=(8, 0))

        decision = ttk.Frame(self.ventana, padding=16, style='Tarjeta.TFrame')
        decision.grid(row=2, column=0, sticky='ew', padx=24, pady=(10, 0))
        self.resumen = tk.StringVar(value='Ingresa una lectura para conocer la acción del agente.')
        self.etiqueta_resumen = ttk.Label(decision, textvariable=self.resumen, style='Accion.TLabel', wraplength=748)
        self.etiqueta_resumen.pack(anchor='w')

        consulta = ttk.Frame(self.ventana, padding=16, style='Tarjeta.TFrame')
        consulta.grid(row=3, column=0, sticky='nsew', padx=24, pady=(10, 0))
        consulta.columnconfigure(0, weight=1)
        consulta.rowconfigure(1, weight=1)
        self.vigencia = tk.StringVar(value='Registros en Atlas · cargando…')
        ttk.Label(consulta, textvariable=self.vigencia, style='Subtitulo.TLabel').grid(row=0, column=0, sticky='w', pady=(0, 8))
        pestanas = ttk.Notebook(consulta)
        pestanas.grid(row=1, column=0, sticky='nsew')
        tabla = ttk.Frame(pestanas)
        detalle = ttk.Frame(pestanas)
        pestanas.add(tabla, text='Registros')
        pestanas.add(detalle, text='Detalle del seleccionado')
        tabla.columnconfigure(0, weight=1)
        tabla.rowconfigure(0, weight=1)
        columnas = ('fecha', 'temperatura', 'humedad', 'accion')
        self.tabla = ttk.Treeview(tabla, columns=columnas, show='headings', selectmode='browse', height=5)
        for nombre, titulo, ancho in [('fecha', 'Fecha (UTC)', 175), ('temperatura', 'Temp. °C', 80),
                                      ('humedad', 'Humedad %', 90), ('accion', 'Acción del agente', 440)]:
            self.tabla.heading(nombre, text=titulo)
            self.tabla.column(nombre, width=ancho, minwidth=70, stretch=nombre == 'accion')
        vertical = ttk.Scrollbar(tabla, orient='vertical', command=self.tabla.yview)
        horizontal = ttk.Scrollbar(tabla, orient='horizontal', command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.grid(row=0, column=0, sticky='nsew')
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        self.tabla.bind('<<TreeviewSelect>>', self.seleccionar_registro)
        detalle.columnconfigure(0, weight=1)
        detalle.rowconfigure(0, weight=1)
        self.documento = ScrolledText(detalle, width=60, height=5, wrap='word',
                                     font=('TkFixedFont', 10), relief='solid', borderwidth=1,
                                     background='#f6f9fb', foreground='#183447', padx=10, pady=8)
        self.documento.insert('1.0', 'Selecciona un registro de la tabla para ver sus datos completos.')
        self.documento.configure(state='disabled')
        self.documento.grid(row=0, column=0, sticky='nsew')
        paginas = ttk.Frame(consulta, style='Tarjeta.TFrame')
        paginas.grid(row=2, column=0, sticky='ew', pady=(6, 0))
        self.boton_anterior = ttk.Button(paginas, text='Anterior', command=lambda: self.cambiar_pagina(-1))
        self.boton_siguiente = ttk.Button(paginas, text='Siguiente', command=lambda: self.cambiar_pagina(1))
        self.paginacion = tk.StringVar(value='Página 1')
        self.boton_anterior.pack(side='left')
        ttk.Label(paginas, textvariable=self.paginacion, style='Tarjeta.TLabel').pack(side='left', padx=12)
        self.boton_siguiente.pack(side='left')

        pie = ttk.Frame(self.ventana, padding=(24, 10, 24, 16))
        pie.grid(row=4, column=0, sticky='ew')
        pie.columnconfigure(0, weight=1)
        self.progreso = ttk.Progressbar(pie, mode='indeterminate')
        self.progreso.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        self.estado = tk.StringVar(value='Consultando tus registros en Atlas…')
        self.etiqueta_estado = ttk.Label(pie, textvariable=self.estado, wraplength=780)
        self.etiqueta_estado.grid(row=1, column=0, sticky='w')

    def _ajustar(self, evento):
        if evento.widget is self.ventana:
            self.etiqueta_resumen.configure(wraplength=max(300, evento.width - 80))
            for etiqueta in (self.etiqueta_destino, self.etiqueta_estado):
                etiqueta.configure(wraplength=max(300, evento.width - 48))

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
        if cambio == -1 and self.pagina > 0:
            self._enviar('listar', pagina=self.pagina - 1)
        elif cambio == 1 and self.hay_siguiente:
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
                                     identificador, self.pagina if pagina is None else pagina), daemon=True).start()
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
                fecha = str(d.get('fecha') or '').replace('T', ' ')[:19]
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
            elif self.seleccionado is not None:
                self._nuevo_formulario()
            self.pendiente_seleccion = None
        finally:
            self.renderizando = False
        self.paginacion.set(f'Página {self.pagina + 1} · {len(self.registros)} registros')
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
            self.vigencia.set('Lista pendiente de actualizar; pulsa Actualizar lista')
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
