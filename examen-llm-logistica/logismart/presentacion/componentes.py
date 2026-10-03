"""Formularios y tablas reutilizables; el usuario nunca necesita editar JSON."""
import json
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText


def texto_detalle(parent, titulo, contenido):
    ventana = tk.Toplevel(parent)
    ventana.title(titulo)
    ventana.geometry('820x600')
    texto = ScrolledText(ventana, wrap='word', padx=12, pady=12)
    texto.pack(fill='both', expand=True)
    texto.insert('1.0', contenido if isinstance(contenido, str) else json.dumps(contenido, ensure_ascii=False, indent=2))
    texto.configure(state='disabled')
    ttk.Button(ventana, text='Cerrar', command=ventana.destroy).pack(pady=8)
    return ventana


class Formulario(tk.Toplevel):
    """Campos: (nombre, etiqueta, tipo, opciones/default)."""
    def __init__(self, app, titulo, campos, valores, guardar, extra=None):
        super().__init__(app.root)
        self.app, self.campos, self.variables, self.textos = app, campos, {}, {}
        self.title(titulo)
        self.geometry('760x690')
        self.minsize(650, 500)
        self.transient(app.root)
        self.grab_set()
        base = ttk.Frame(self, padding=12)
        base.pack(fill='both', expand=True)
        canvas = tk.Canvas(base, highlightthickness=0)
        scroll = ttk.Scrollbar(base, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        self.contenido = ttk.Frame(canvas, padding=6)
        item = canvas.create_window((0, 0), window=self.contenido, anchor='nw')
        self.contenido.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(item, width=e.width))
        self.contenido.columnconfigure(1, weight=1)
        for fila, (nombre, etiqueta, tipo, opciones) in enumerate(campos):
            ttk.Label(self.contenido, text=etiqueta, wraplength=200).grid(row=fila, column=0, sticky='nw', padx=(0, 12), pady=6)
            valor = valores.get(nombre, False if tipo == 'bool' else '')
            if valor is None: valor = ''
            if tipo == 'texto':
                widget = ScrolledText(self.contenido, height=4, width=42, wrap='word')
                widget.insert('1.0', str(valor))
                self.textos[nombre] = widget
            else:
                var = tk.BooleanVar(value=bool(valor)) if tipo == 'bool' else tk.StringVar(value=str(valor))
                self.variables[nombre] = var
                if tipo == 'bool':
                    widget = ttk.Checkbutton(self.contenido, variable=var)
                elif tipo == 'opcion':
                    widget = ttk.Combobox(self.contenido, textvariable=var, values=opciones, state='readonly')
                    if not str(valor) and opciones: var.set(opciones[0])
                else:
                    widget = ttk.Entry(self.contenido, textvariable=var)
            widget.grid(row=fila, column=1, sticky='ew', pady=6)
        self.extra = ttk.Frame(self.contenido)
        self.extra.grid(row=len(campos), column=0, columnspan=2, sticky='ew', pady=10)
        if extra: extra(self)
        pie = ttk.Frame(self, padding=12)
        pie.pack(fill='x')
        self.boton_guardar = ttk.Button(pie, text='Guardar', command=lambda: self._guardar(guardar))
        self.boton_guardar.pack(side='right')
        ttk.Button(pie, text='Cancelar', command=self.cancelar).pack(side='right', padx=8)
        self.protocol('WM_DELETE_WINDOW', self.cancelar)

    def leer(self):
        resultado = {}
        for nombre, etiqueta, tipo, _ in self.campos:
            valor = self.textos[nombre].get('1.0', 'end').strip() if tipo == 'texto' else self.variables[nombre].get()
            try:
                if tipo == 'entero': valor = int(valor)
                elif tipo in {'decimal', 'decimal_opcional'}:
                    valor = None if tipo == 'decimal_opcional' and not valor else float(str(valor).replace(',', '.'))
                elif tipo == 'opcional' and not valor: valor = None
            except ValueError:
                raise ValueError(f'El campo «{etiqueta}» debe contener un número válido.') from None
            resultado[nombre] = valor
        return resultado

    def _guardar(self, callback):
        try:
            datos = self.leer()
            callback(self, datos)
        except (ValueError, TypeError) as error:
            messagebox.showerror('Revisa el formulario', str(error), parent=self)

    def cancelar(self):
        if self.app.trabajos.ocupado:
            messagebox.showinfo('Operación en curso', 'Espera a que termine antes de cerrar el formulario.', parent=self)
        else:
            self.destroy()


class Tabla(ttk.Frame):
    def __init__(self, parent, columnas, altura=14):
        super().__init__(parent)
        self.columnas = columnas
        self.tree = ttk.Treeview(self, columns=[k for k, _ in columnas], show='headings', height=altura)
        for nombre, etiqueta in columnas:
            self.tree.heading(nombre, text=etiqueta)
            self.tree.column(nombre, width=160, minwidth=90, stretch=True)
        vertical = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        horizontal = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.registros = {}

    def mostrar(self, registros, valores=None):
        self.tree.delete(*self.tree.get_children())
        self.registros = {}
        for i, d in enumerate(registros):
            identificador = str(d.get('_id', i))
            self.registros[identificador] = d
            fila = valores(d) if valores else [d.get(k, '') for k, _ in self.columnas]
            self.tree.insert('', 'end', iid=identificador, values=fila)

    def seleccionado(self):
        seleccion = self.tree.selection()
        if not seleccion:
            raise ValueError('Selecciona un registro de la tabla.')
        return self.registros[seleccion[0]]


class PaginaCRUD(ttk.Frame):
    def __init__(self, app, parent, titulo, coleccion, columnas, abrir, valores=None):
        super().__init__(parent, padding=14)
        self.app, self.coleccion, self.abrir = app, coleccion, abrir
        self.valores = valores
        ttk.Label(self, text=titulo, font=('TkDefaultFont', 17, 'bold')).pack(anchor='w')
        self.barra = ttk.Frame(self)
        self.barra.pack(fill='x', pady=12)
        for etiqueta, accion in [('Nuevo', lambda: self.editar(False)), ('Editar', lambda: self.editar(True)),
                                 ('Eliminar', self.eliminar), ('Actualizar', self.actualizar), ('Detalle e historial', self.detalle)]:
            ttk.Button(self.barra, text=etiqueta, command=accion).pack(side='left', padx=(0, 6))
        self.tabla = Tabla(self, columnas)
        self.tabla.pack(fill='both', expand=True)
        self.conteo = tk.StringVar(value='Pulsa Actualizar para consultar los registros.')
        ttk.Label(self, textvariable=self.conteo).pack(anchor='w', pady=8)

    def actualizar(self):
        def listo(datos):
            self.tabla.mostrar(datos, self.valores)
            self.conteo.set(f'{len(datos)} registros activos · Horas en UTC')
            if hasattr(self, 'al_actualizar'): self.al_actualizar(datos)
        self.app.trabajos.ejecutar('Consultando registros…', lambda: self.app.servicio.repo.listar(self.coleccion), listo)

    def editar(self, existente):
        if self.app.trabajos.ocupado: return
        try:
            anterior = self.tabla.seleccionado() if existente else None
            self.abrir(self, anterior)
        except ValueError as error:
            messagebox.showinfo('Selección', str(error), parent=self)

    def detalle(self):
        try:
            texto_detalle(self, 'Registro e historial de cambios', self.tabla.seleccionado())
        except ValueError as error:
            messagebox.showinfo('Selección', str(error), parent=self)

    def eliminar(self):
        if self.app.trabajos.ocupado: return
        try:
            d = self.tabla.seleccionado()
        except ValueError as error:
            messagebox.showinfo('Selección', str(error), parent=self)
            return
        if messagebox.askyesno('Confirmar baja', f"¿Dar de baja el registro {d['_id']}?\nSe conservará el historial para auditoría.", default='no', parent=self):
            self.app.trabajos.ejecutar('Guardando baja…',
                lambda: self.app.servicio.repo.eliminar(self.coleccion, d['_id'], self.app.config.operador, d['version']),
                lambda _: self.actualizar())
