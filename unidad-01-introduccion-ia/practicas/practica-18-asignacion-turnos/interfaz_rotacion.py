"""Pestaña de rotación independiente del algoritmo de optimización inicial."""
import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from asignacion import EMPLEADOS
from rotacion import MODOS, generar_rotacion, guardar_csv
from graficas import dibujar_rotacion, guardar_rotacion_png


class PanelRotacion(ttk.Frame):
    def __init__(self, parent, modo="completa", periodos=4):
        super().__init__(parent, padding=12)
        self.base = None
        self.calendario = None
        self.pendiente = True
        self.actual = 0
        self.modo = tk.StringVar(value=MODOS[modo])
        self.cantidad = tk.StringVar(value=str(periodos))
        self.estado = tk.StringVar()
        self.resumen = tk.StringVar()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        opciones = ttk.Frame(self)
        opciones.grid(row=0, column=0, sticky="ew")
        ttk.Label(opciones, text="Rotación:").pack(side="left", padx=(0, 6))
        self.selector = ttk.Combobox(opciones, textvariable=self.modo, values=list(MODOS.values()),
                                    state="readonly", width=34)
        self.selector.pack(side="left", padx=(0, 12))
        ttk.Label(opciones, text="Periodos:").pack(side="left", padx=(0, 6))
        self.contador = ttk.Spinbox(opciones, from_=1, to=52, textvariable=self.cantidad, width=4)
        self.contador.pack(side="left")

        controles = ttk.Frame(self)
        controles.grid(row=1, column=0, sticky="ew", pady=8)
        self.generar = ttk.Button(controles, text="Generar calendario", command=self.calcular)
        self.anterior = ttk.Button(controles, text="Anterior", command=lambda: self.rolar(-1))
        self.siguiente = ttk.Button(controles, text="Rolar al siguiente", command=lambda: self.rolar(1))
        self.csv = ttk.Button(controles, text="Exportar CSV", command=self.exportar)
        self.png = ttk.Button(controles, text="Gráfica PNG", command=lambda: self.exportar(imagen=True))
        for boton in (self.generar, self.anterior, self.siguiente, self.csv, self.png):
            boton.pack(side="left", padx=(0, 5))
        ttk.Label(self, textvariable=self.estado, wraplength=700).grid(row=2, column=0, sticky="w", pady=(0, 8))

        marco = ttk.Frame(self)
        marco.grid(row=3, column=0, sticky="ew")
        marco.columnconfigure(0, weight=1)
        columnas = ("Periodo", *EMPLEADOS, "Cumplidas", "Satisfacción")
        self.tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=4)
        for nombre in columnas:
            self.tabla.heading(nombre, text=nombre)
            self.tabla.column(nombre, width=90, minwidth=65, anchor="center")
        self.tabla.grid(row=0, column=0, sticky="ew")
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        barra.grid(row=0, column=1, sticky="ns")
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar)
        ttk.Label(self, textvariable=self.resumen).grid(row=4, column=0, sticky="w", pady=8)

        self.figura = Figure(figsize=(8, 3.4), dpi=100, layout="constrained")
        self.lienzo = FigureCanvasTkAgg(self.figura, master=self)
        widget = self.lienzo.get_tk_widget()
        widget.grid(row=5, column=0, sticky="nsew")
        widget.bind("<Map>", lambda _: widget.after_idle(
            lambda: widget.event_generate("<Configure>", width=widget.winfo_width(), height=widget.winfo_height())), add="+")
        self.modo.trace_add("write", self.marcar_pendiente)
        self.cantidad.trace_add("write", self.marcar_pendiente)
        self.actualizar_botones()

    def actualizar_botones(self):
        valido = self.base is not None and self.calendario is not None and not self.pendiente
        self.generar.configure(state="normal" if self.base is not None else "disabled")
        self.anterior.configure(state="normal" if valido and self.actual > 0 else "disabled")
        self.siguiente.configure(state="normal" if valido and self.actual < len(self.calendario.periodos)-1 else "disabled")
        for boton in (self.csv, self.png):
            boton.configure(state="normal" if valido else "disabled")

    def marcar_pendiente(self, *_):
        self.pendiente = True
        self.estado.set("Hay cambios pendientes. Pulsa Generar calendario para actualizar la tabla y la gráfica.")
        self.actualizar_botones()

    def invalidar_base(self):
        self.base = None
        self.marcar_pendiente()
        self.estado.set("El inicio cambió. Pulsa Asignar turnos para recalcular antes de rolar.")

    def actualizar_base(self, base):
        self.base = base
        return self.calcular()

    def calcular(self):
        if self.base is None:
            return False
        try:
            cantidad = int(self.cantidad.get())
            modo = next(clave for clave, valor in MODOS.items() if valor == self.modo.get())
            calendario = generar_rotacion(self.base, cantidad, modo)
        except (ValueError, StopIteration) as error:
            self.marcar_pendiente()
            self.estado.set(str(error) if isinstance(error, ValueError) and "invalid literal" not in str(error)
                            else "Elige un modo válido y una cantidad entera de 1 a 52 periodos.")
            return False
        self.calendario, self.pendiente, self.actual = calendario, False, 0
        self.tabla.delete(*self.tabla.get_children())
        for indice, periodo in enumerate(calendario.periodos):
            self.tabla.insert("", "end", iid=str(indice), values=(periodo.numero, *periodo.asignacion,
                              f"{periodo.satisfaccion}/4", f"{periodo.satisfaccion / 4:.0%}"))
        self.estado.set("Cada empleado pasa por los cuatro turnos. En un ciclo de 4 periodos, cada uno cumple su preferencia una vez."
                        if modo == "completa" else
                        "Ana y María alternan Mañana/Mixto. Luis conserva Tarde y Carlos Noche: 75 % por periodo.")
        self.tabla.selection_set("0")
        self.tabla.focus("0")
        self.tabla.see("0")
        self.mostrar()
        return True

    def seleccionar(self, _=None):
        seleccion = self.tabla.selection()
        if self.pendiente or not seleccion:
            return
        self.actual = int(seleccion[0])
        self.mostrar()

    def mostrar(self):
        periodo = self.calendario.periodos[self.actual]
        self.resumen.set(f"Periodo {periodo.numero}: {periodo.satisfaccion}/4 preferencias · "
                         f"Promedio de los {len(self.calendario.periodos)} periodos: {self.calendario.porcentaje:.1f} %")
        dibujar_rotacion(self.figura, self.calendario, self.actual)
        self.lienzo.draw_idle()
        self.actualizar_botones()

    def rolar(self, cambio):
        if self.pendiente or self.calendario is None:
            return
        self.actual = min(max(0, self.actual + cambio), len(self.calendario.periodos)-1)
        clave = str(self.actual)
        self.tabla.selection_set(clave)
        self.tabla.focus(clave)
        self.tabla.see(clave)
        self.mostrar()

    def exportar(self, imagen=False):
        if self.pendiente or self.calendario is None:
            self.estado.set("Genera un calendario válido antes de exportar.")
            return
        extension = ".png" if imagen else ".csv"
        destino = filedialog.asksaveasfilename(parent=self, title="Guardar rotación de turnos",
                    initialfile="Rotacion_turnos"+extension, defaultextension=extension,
                    filetypes=[("Imagen PNG" if imagen else "Tabla CSV", "*"+extension)])
        if not destino:
            return
        try:
            ruta = guardar_rotacion_png(destino, self.calendario, self.actual) if imagen else guardar_csv(self.calendario, destino)
        except (OSError, ValueError) as error:
            self.estado.set(f"No se pudo guardar el archivo: {error}")
            return
        self.estado.set(f"Archivo guardado: {ruta}")
