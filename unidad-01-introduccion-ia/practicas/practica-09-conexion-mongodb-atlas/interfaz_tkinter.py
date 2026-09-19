"""Ventana de la práctica 9. Los widgets se actualizan solo en el hilo principal."""

import json
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from servicio_atlas import ErrorAtlas, ServicioAtlas, validar_dato


def ejecutar_operacion(servicio, accion, dato, resultados):
    """Trabajar con Atlas en segundo plano sin acceder a ningún widget."""
    try:
        respuesta = (servicio.guardar(dato) if accion == 'guardar'
                     else {'ok': True, 'documento': servicio.consultar(),
                           'mensaje': 'Consulta completada.'})
    except ErrorAtlas as error:
        respuesta = {'ok': False, 'mensaje': str(error), 'guardado': error.guardado}
    except Exception:
        # No publicar mensajes internos que puedan incluir credenciales.
        respuesta = {'ok': False, 'mensaje': 'No se pudo completar la operación. '
                     'Pulsa Actualizar para consultar Atlas antes de reintentar.'}
    resultados.put({**respuesta, 'base': servicio.base, 'coleccion': servicio.coleccion})


class VentanaAtlas:
    def __init__(self, ventana, servicio=None):
        self.ventana = ventana
        self.servicio = servicio if servicio is not None else ServicioAtlas()
        self.resultados = Queue()
        self.ocupado = False
        self.cerrando = False
        self.cerrada = False
        self.sondeo = None
        self.ventana.title('Práctica 9 · MongoDB Atlas')
        self.ventana.geometry('900x660')
        self.ventana.minsize(760, 600)
        self.ventana.configure(background='#eef4f0')
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(1, weight=1)
        self._crear_interfaz()
        self.ventana.protocol('WM_DELETE_WINDOW', self.cerrar)
        self.ventana.bind('<Control-Return>', lambda evento: self.guardar())
        self.ventana.bind('<Configure>', self._ajustar_textos)
        self.entrada.focus_set()
        self.actualizar()

    def _crear_interfaz(self):
        estilo = ttk.Style(self.ventana)
        if 'clam' in estilo.theme_names():
            estilo.theme_use('clam')
        estilo.configure('TFrame', background='#eef4f0')
        estilo.configure('Tarjeta.TFrame', background='#ffffff')
        estilo.configure('TLabel', background='#eef4f0', foreground='#173d2a', font=('TkDefaultFont', 10))
        estilo.configure('Titulo.TLabel', font=('TkDefaultFont', 23, 'bold'))
        estilo.configure('Tarjeta.TLabel', background='#ffffff')
        estilo.configure('Subtitulo.TLabel', background='#ffffff', font=('TkDefaultFont', 13, 'bold'))
        estilo.configure('TButton', padding=(14, 9), font=('TkDefaultFont', 10))
        estilo.configure('Guardar.TButton', background='#176943', foreground='#ffffff')
        estilo.map('Guardar.TButton', background=[('disabled', '#dae6de'), ('active', '#114f32')],
                   foreground=[('disabled', '#56665c')])

        cabecera = ttk.Frame(self.ventana, padding=(24, 22, 24, 14))
        cabecera.grid(row=0, column=0, sticky='ew')
        ttk.Label(cabecera, text='PRÁCTICA 09  /  FUNDAMENTOS DE IA').pack(anchor='w')
        ttk.Label(cabecera, text='Mi dato en MongoDB Atlas', style='Titulo.TLabel').pack(anchor='w', pady=(5, 7))
        ttk.Label(cabecera, text='Einar Ivan Lazcano Luna · Interfaz con Tkinter').pack(anchor='w')
        self.destino = tk.StringVar(value='Leyendo la configuración del .env…')
        self.etiqueta_destino = ttk.Label(cabecera, textvariable=self.destino, wraplength=840)
        self.etiqueta_destino.pack(anchor='w', pady=(10, 0))

        cuerpo = ttk.Frame(self.ventana, padding=(24, 0, 24, 0))
        cuerpo.grid(row=1, column=0, sticky='nsew')
        cuerpo.columnconfigure(0, weight=1, uniform='panel')
        cuerpo.columnconfigure(1, weight=1, uniform='panel')
        cuerpo.rowconfigure(0, weight=1)
        formulario = ttk.Frame(cuerpo, padding=18, style='Tarjeta.TFrame')
        formulario.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        formulario.columnconfigure(0, weight=1)
        formulario.rowconfigure(2, weight=1)
        ttk.Label(formulario, text='1. Escribe tu dato', style='Subtitulo.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(formulario, text='Puedes guardar una nota de hasta 1000 caracteres.',
                  style='Tarjeta.TLabel', wraplength=315).grid(row=1, column=0, sticky='w', pady=(8, 12))
        self.entrada = ScrolledText(formulario, width=30, height=7, wrap='word', undo=True,
                                   font=('TkDefaultFont', 11), relief='solid', borderwidth=1,
                                   background='#fafcfb', foreground='#162e21', padx=10, pady=10)
        self.entrada.grid(row=2, column=0, sticky='nsew')
        self.contador = tk.StringVar(value='0 / 1000 caracteres')
        ttk.Label(formulario, textvariable=self.contador, style='Tarjeta.TLabel').grid(row=3, column=0, sticky='e', pady=(6, 12))
        self.entrada.bind('<<Modified>>', self._contar)
        self.boton_guardar = ttk.Button(formulario, text='Guardar en Atlas', command=self.guardar, style='Guardar.TButton')
        self.boton_guardar.grid(row=4, column=0, sticky='ew')
        self.boton_limpiar = ttk.Button(formulario, text='Limpiar formulario', command=self.limpiar)
        self.boton_limpiar.grid(row=5, column=0, sticky='ew', pady=(8, 0))
        ttk.Label(formulario, text='Cada guardado actualiza el mismo documento.\nAtajo: Ctrl + Enter.',
                  style='Tarjeta.TLabel', wraplength=315).grid(row=6, column=0, sticky='w', pady=(12, 0))

        consulta = ttk.Frame(cuerpo, padding=18, style='Tarjeta.TFrame')
        consulta.grid(row=0, column=1, sticky='nsew', padx=(8, 0))
        consulta.columnconfigure(0, weight=1)
        consulta.rowconfigure(2, weight=1)
        ttk.Label(consulta, text='2. Documento en Atlas', style='Subtitulo.TLabel').grid(row=0, column=0, sticky='w')
        self.vigencia = tk.StringVar(value='Esperando la primera consulta…')
        ttk.Label(consulta, textvariable=self.vigencia, style='Tarjeta.TLabel',
                  wraplength=315).grid(row=1, column=0, sticky='w', pady=(8, 12))
        self.documento = ScrolledText(consulta, width=30, height=10, wrap='word',
                                     font=('TkFixedFont', 10), state='disabled',
                                     relief='solid', borderwidth=1, background='#f5f8f6',
                                     foreground='#162e21', padx=10, pady=10)
        self.documento.grid(row=2, column=0, sticky='nsew')
        self.boton_actualizar = ttk.Button(consulta, text='Actualizar consulta', command=self.actualizar)
        self.boton_actualizar.grid(row=3, column=0, sticky='ew', pady=(12, 0))
        self.botones = (self.boton_guardar, self.boton_limpiar, self.boton_actualizar)

        pie = ttk.Frame(self.ventana, padding=(24, 12, 24, 18))
        pie.grid(row=2, column=0, sticky='ew')
        pie.columnconfigure(0, weight=1)
        self.progreso = ttk.Progressbar(pie, mode='indeterminate')
        self.progreso.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        self.estado = tk.StringVar(value='Lista para consultar Atlas.')
        self.etiqueta_estado = ttk.Label(pie, textvariable=self.estado, wraplength=840)
        self.etiqueta_estado.grid(row=1, column=0, sticky='w')

    def _ajustar_textos(self, evento):
        if evento.widget is self.ventana:
            ancho = max(300, evento.width - 48)
            self.etiqueta_estado.configure(wraplength=ancho)
            self.etiqueta_destino.configure(wraplength=ancho)

    def _contar(self, evento=None):
        if self.entrada.edit_modified():
            cantidad = len(self.entrada.get('1.0', 'end-1c').strip())
            self.contador.set(f'{cantidad} / 1000 caracteres')
            self.entrada.edit_modified(False)

    def _mensaje(self, texto, error=False):
        self.estado.set(texto)
        self.etiqueta_estado.configure(foreground='#a12622' if error else '#173d2a')

    def limpiar(self):
        if self.ocupado or self.cerrando:
            return
        self.entrada.delete('1.0', 'end')
        self.contador.set('0 / 1000 caracteres')
        self.entrada.focus_set()
        self._mensaje('Formulario vacío. El documento de Atlas se conserva.')

    def guardar(self):
        if self.ocupado or self.cerrando:
            return
        try:
            dato = validar_dato(self.entrada.get('1.0', 'end-1c'))
        except ErrorAtlas as error:
            self._mensaje(str(error), error=True)
            self.entrada.focus_set()
            return
        self._enviar('guardar', dato)

    def actualizar(self):
        self._enviar('consultar')

    def _enviar(self, accion, dato=None):
        if self.ocupado or self.cerrando or self.cerrada:
            return
        self.ocupado = True
        for boton in self.botones:
            boton.state(['disabled'])
        self.entrada.configure(state='disabled')
        self.progreso.start(12)
        self._mensaje('Guardando tu dato en Atlas…' if accion == 'guardar' else 'Consultando Atlas…')
        Thread(target=ejecutar_operacion,
               args=(self.servicio, accion, dato, self.resultados), daemon=True).start()
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
            self.destino.set(f"Base: {respuesta['base']}\nColección: {respuesta['coleccion']}")
        if respuesta['ok']:
            documento = respuesta['documento']
            contenido = (json.dumps(documento, ensure_ascii=False, indent=2) if documento is not None
                         else 'Todavía no hay un documento.\nEscribe tu dato y pulsa Guardar en Atlas.')
            self.documento.configure(state='normal')
            self.documento.delete('1.0', 'end')
            self.documento.insert('1.0', contenido)
            self.documento.configure(state='disabled')
            self.vigencia.set('Documento consultado en Atlas.' if documento else 'Sin documento guardado.')
        else:
            self.vigencia.set('Última consulta: puede estar desactualizada.')
        self._mensaje(respuesta['mensaje'], error=not respuesta['ok'])
        if self.cerrando:
            self.cerrar()
            return
        for boton in self.botones:
            boton.state(['!disabled'])
        self.entrada.configure(state='normal')

    def cerrar(self):
        if self.cerrada:
            return
        self.cerrando = True
        if self.ocupado:
            self._mensaje('Esperando que termine la operación para cerrar la ventana…')
            return
        if self.sondeo is not None:
            self.ventana.after_cancel(self.sondeo)
        self.servicio.cerrar()
        self.cerrada = True
        self.ventana.destroy()


def main():
    try:
        ventana = tk.Tk()
    except tk.TclError:
        print('No se pudo abrir la ventana. Comprueba Tkinter y el soporte gráfico de WSL (WSLg).')
        print('Prueba: python3 -m tkinter. Consulta el README de la práctica 9.')
        return 1
    app = VentanaAtlas(ventana)
    try:
        ventana.mainloop()
    finally:
        app.servicio.cerrar()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
