"""Interfaz Tkinter: percibir y decidir en pantalla; registrar en segundo plano."""

import json
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from agente_climatizacion import AgenteClimatizacion
from almacenamiento_atlas import AlmacenamientoAtlas, ErrorAtlas


def trabajar(almacenamiento, operacion, agente, resultados):
    """Este hilo trabaja con el agente y Atlas; no accede a widgets."""
    try:
        if operacion == 'guardar':
            documento = agente.ejecutar(almacenamiento)
            mensaje = 'Registro insertado y confirmado por Atlas.'
        else:
            documento = almacenamiento.consultar_ultimo()
            mensaje = 'Último registro consultado.' if documento else 'Todavía no hay registros de la práctica 10.'
        respuesta = {'ok': True, 'documento': documento, 'mensaje': mensaje}
    except (ErrorAtlas, ValueError) as error:
        respuesta = {'ok': False, 'mensaje': str(error)}
    except Exception:
        respuesta = {'ok': False, 'mensaje': 'No se pudo completar la operación. '
                     'Consulta el último registro antes de reintentar.'}
    resultados.put({**respuesta, 'operacion': operacion,
                    'base': almacenamiento.base, 'coleccion': almacenamiento.coleccion})


class VentanaClimatizacion:
    def __init__(self, ventana, almacenamiento=None):
        self.ventana = ventana
        self.almacenamiento = almacenamiento if almacenamiento is not None else AlmacenamientoAtlas()
        self.resultados = Queue()
        self.ocupado = self.cerrando = self.cerrada = False
        self.sondeo = None
        self.ventana.title('Práctica 10 · Agente de climatización')
        self.ventana.geometry('840x720')
        self.ventana.minsize(720, 650)
        self.ventana.configure(background='#eef3f7')
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(3, weight=1)
        self._crear_interfaz()
        self.ventana.protocol('WM_DELETE_WINDOW', self.cerrar)
        self.ventana.bind('<Control-Return>', lambda evento: self.evaluar_y_guardar())
        self.ventana.bind('<Configure>', self._ajustar)
        self.temperatura.trace_add('write', self._lectura_modificada)
        self.humedad.trace_add('write', self._lectura_modificada)
        self.entrada_temperatura.focus_set()

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
        ttk.Label(cabecera, text='Percibir → decidir → registrar en Atlas · Einar Ivan Lazcano Luna').pack(anchor='w')
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
        self.boton_guardar = ttk.Button(botones, text='Evaluar y guardar', command=self.evaluar_y_guardar, style='Guardar.TButton')
        self.boton_consultar = ttk.Button(botones, text='Consultar último registro', command=self.consultar)
        self.boton_limpiar = ttk.Button(botones, text='Limpiar', command=self.limpiar)
        for columna, boton in enumerate((self.boton_guardar, self.boton_consultar, self.boton_limpiar)):
            boton.grid(row=0, column=columna, padx=(0, 8), sticky='ew')
        botones.columnconfigure(0, weight=1)
        botones.columnconfigure(1, weight=1)
        self.botones = (self.boton_guardar, self.boton_consultar, self.boton_limpiar)
        self.entradas = (self.entrada_temperatura, self.entrada_humedad)

        decision = ttk.Frame(self.ventana, padding=16, style='Tarjeta.TFrame')
        decision.grid(row=2, column=0, sticky='ew', padx=24, pady=(10, 0))
        self.resumen = tk.StringVar(value='Ingresa una lectura para conocer la acción del agente.')
        self.etiqueta_resumen = ttk.Label(decision, textvariable=self.resumen, style='Accion.TLabel', wraplength=748)
        self.etiqueta_resumen.pack(anchor='w')

        consulta = ttk.Frame(self.ventana, padding=16, style='Tarjeta.TFrame')
        consulta.grid(row=3, column=0, sticky='nsew', padx=24, pady=(10, 0))
        consulta.columnconfigure(0, weight=1)
        consulta.rowconfigure(1, weight=1)
        self.vigencia = tk.StringVar(value='Registro en Atlas · sin consulta realizada')
        ttk.Label(consulta, textvariable=self.vigencia, style='Subtitulo.TLabel').grid(row=0, column=0, sticky='w', pady=(0, 8))
        self.documento = ScrolledText(consulta, width=60, height=7, wrap='word',
                                     font=('TkFixedFont', 10), relief='solid', borderwidth=1,
                                     background='#f6f9fb', foreground='#183447', padx=10, pady=8)
        self.documento.insert('1.0', 'El registro confirmado aparecerá aquí con su identificador de MongoDB.')
        self.documento.configure(state='disabled')
        self.documento.grid(row=1, column=0, sticky='nsew')

        pie = ttk.Frame(self.ventana, padding=(24, 10, 24, 16))
        pie.grid(row=4, column=0, sticky='ew')
        pie.columnconfigure(0, weight=1)
        self.progreso = ttk.Progressbar(pie, mode='indeterminate')
        self.progreso.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        self.estado = tk.StringVar(value='Lista. Cada evaluación guarda un registro nuevo.')
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
        if not self.ocupado:
            self.resumen.set('Lectura modificada. Pulsa Evaluar y guardar para calcular la nueva acción.')

    def evaluar_y_guardar(self):
        if self.ocupado or self.cerrando or self.cerrada:
            return
        agente = AgenteClimatizacion()
        try:
            agente.percibir(self.temperatura.get(), self.humedad.get())
            agente.tomar_decision()
        except ValueError as error:
            self._mensaje(str(error), error=True)
            entrada = self.entrada_humedad if 'humedad' in str(error) else self.entrada_temperatura
            entrada.focus_set()
            return
        self.resumen.set(agente.mostrar_resultado())
        self._enviar('guardar', agente)

    def consultar(self):
        self._enviar('consultar')

    def limpiar(self):
        if self.ocupado or self.cerrando or self.cerrada:
            return
        self.temperatura.set('')
        self.humedad.set('')
        self.resumen.set('Ingresa una lectura para conocer la acción del agente.')
        self._mensaje('Formulario limpio. Los registros de Atlas se conservan.')
        self.entrada_temperatura.focus_set()

    def _enviar(self, operacion, agente=None):
        if self.ocupado or self.cerrando or self.cerrada:
            return
        self.ocupado = True
        for control in (*self.botones, *self.entradas):
            control.state(['disabled'])
        self.progreso.start(12)
        self._mensaje('Decisión calculada. Guardando en Atlas…' if operacion == 'guardar' else 'Consultando Atlas…')
        Thread(target=trabajar, args=(self.almacenamiento, operacion, agente, self.resultados), daemon=True).start()
        self.sondeo = self.ventana.after(80, self._recibir)

    def _recibir(self):
        self.sondeo = None
        try:
            respuesta = self.resultados.get_nowait()
        except Empty:
            self.sondeo = self.ventana.after(80, self._recibir)
            return
        self.ocupado = False
        self.progreso.stop()
        if respuesta['base'] and respuesta['coleccion']:
            self.destino.set(f"Base: {respuesta['base']} · Colección: {respuesta['coleccion']}")
        if respuesta['ok']:
            documento = respuesta['documento']
            contenido = (json.dumps(documento, ensure_ascii=False, indent=2, default=str)
                         if documento is not None else 'No hay registros de la práctica 10 en esta colección.')
            self.documento.configure(state='normal')
            self.documento.delete('1.0', 'end')
            self.documento.insert('1.0', contenido)
            self.documento.configure(state='disabled')
            self.vigencia.set('Registro insertado · confirmado por Atlas' if respuesta['operacion'] == 'guardar'
                              else 'Último registro consultado en Atlas')
        else:
            self.vigencia.set('Último resultado · puede estar desactualizado')
        self._mensaje(respuesta['mensaje'], error=not respuesta['ok'])
        if self.cerrando:
            self.cerrar()
            return
        for control in (*self.botones, *self.entradas):
            control.state(['!disabled'])

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
