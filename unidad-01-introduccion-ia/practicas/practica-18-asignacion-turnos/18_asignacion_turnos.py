"""Práctica 18: asignación de horarios con Hill Climbing, Tkinter y Matplotlib."""
import argparse
from pathlib import Path

from asignacion import (
    EMPLEADOS, TURNOS, PREFERENCIAS, INICIO, descripcion, hill_climbing,
    puntuar, validar_asignacion, verificar_optimas,
)


SALIDA = Path(__file__).resolve().parent / "salidas" / "Asignacion_turnos.png"


def imprimir(resultado, verificacion):
    print("\nPRÁCTICA 18 · ASIGNACIÓN DE TURNOS")
    print("Un empleado por turno. Un punto por cada preferencia cumplida.")
    print("\nEmpleado | Preferencia")
    for empleado, preferencia in zip(EMPLEADOS, PREFERENCIAS):
        print(f"{empleado} | {preferencia}")
    print("\nBúsqueda local: intercambiar los turnos de dos empleados.")
    for i, paso in enumerate(resultado.pasos):
        movimiento = "Inicio" if paso.intercambio is None else "Intercambiar " + " y ".join(paso.intercambio)
        print(f"Paso {i}: {movimiento} · Satisfacción {paso.satisfaccion}/4")
        print(" ", descripcion(paso.asignacion))
    print("Parada: ningún intercambio mejora estrictamente la satisfacción.")
    print(f"\nVerificación independiente: {verificacion.examinadas} asignaciones posibles.")
    print(f"Máximo: {verificacion.satisfaccion}/4 ({verificacion.satisfaccion / 4:.0%}).")
    for i, asignacion in enumerate(verificacion.asignaciones, 1):
        print(f"Óptima {i}: {descripcion(asignacion)}")
    print("Ana y María prefieren Mañana; solo hay una plaza en ese turno.")
    print("Mixto no cuenta como coincidencia con Mañana, Tarde o Noche.")


def crear_interfaz(raiz, inicio=INICIO):
    import tkinter as tk
    from tkinter import ttk, filedialog
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from graficas import dibujar, guardar_png

    class Aplicacion:
        def __init__(self):
            self.inicio_actual = validar_asignacion(inicio)
            self.entradas = [tk.StringVar(value=t) for t in self.inicio_actual]
            self.estado, self.resumen = tk.StringVar(), tk.StringVar()
            self.opcion = tk.StringVar()
            self.pendiente = False
            raiz.title("Práctica 18 · Asignación de turnos")
            raiz.geometry("1280x820")
            raiz.minsize(1120, 760)
            estilo = ttk.Style(raiz)
            estilo.theme_use("clam")
            estilo.configure("TFrame", background="#f5f8fc")
            estilo.configure("TLabel", background="#f5f8fc", foreground="#20354e", font=("DejaVu Sans", 10))
            estilo.configure("Titulo.TLabel", font=("DejaVu Sans", 23, "bold"))
            estilo.configure("Seccion.TLabel", font=("DejaVu Sans", 12, "bold"))
            estilo.configure("Resultado.TLabel", foreground="#147460", font=("DejaVu Sans", 18, "bold"))
            estilo.configure("TButton", padding=(10, 7), font=("DejaVu Sans", 10))
            estilo.configure("Treeview", rowheight=28, font=("DejaVu Sans", 10))
            principal = ttk.Frame(raiz, padding=20)
            principal.pack(fill="both", expand=True)
            principal.columnconfigure(1, weight=1)
            principal.rowconfigure(1, weight=1)
            cabecera = ttk.Frame(principal)
            cabecera.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
            ttk.Label(cabecera, text="UTVT · FUNDAMENTOS DE IA · PRÁCTICA 18").pack(anchor="w")
            ttk.Label(cabecera, text="Un turno para cada empleado", style="Titulo.TLabel").pack(anchor="w", pady=5)
            ttk.Label(cabecera, text="Hill Climbing · Intercambiar horarios · Maximizar preferencias cumplidas").pack(anchor="w")

            self.panel = ttk.Frame(principal, padding=(0, 0, 18, 0))
            self.panel.grid(row=1, column=0, sticky="nsw")
            ttk.Label(self.panel, text="Preferencias del ejercicio", style="Seccion.TLabel").pack(anchor="w", pady=(0, 8))
            self.tabla_preferencias = self.tabla(self.panel, (("empleado", "Empleado", 125), ("preferencia", "Preferencia", 140)), 4)
            for nombre, preferencia in zip(EMPLEADOS, PREFERENCIAS):
                self.tabla_preferencias.insert("", "end", values=(nombre, preferencia))
            ttk.Label(self.panel, text="Asignación inicial", style="Seccion.TLabel").pack(anchor="w", pady=(16, 8))
            formulario = ttk.Frame(self.panel)
            formulario.pack(fill="x")
            self.selectores = []
            for i, nombre in enumerate(EMPLEADOS):
                ttk.Label(formulario, text=nombre).grid(row=i, column=0, sticky="w", padx=(0, 14), pady=5)
                selector = ttk.Combobox(formulario, values=TURNOS, textvariable=self.entradas[i], state="readonly", width=17)
                selector.grid(row=i, column=1, sticky="w")
                selector.bind("<<ComboboxSelected>>", lambda evento, indice=i: self.intercambiar_inicio(indice))
                self.selectores.append(selector)
            ttk.Label(self.panel, text="Cambiar un turno intercambia automáticamente con quien lo ocupa.", wraplength=280).pack(anchor="w", pady=8)
            botones = ttk.Frame(self.panel)
            botones.pack(fill="x", pady=6)
            self.boton_buscar = ttk.Button(botones, text="Asignar turnos", command=self.calcular)
            self.boton_buscar.pack(side="left", padx=(0, 8))
            ttk.Button(botones, text="Restablecer", command=self.restablecer).pack(side="left")
            ttk.Separator(self.panel).pack(fill="x", pady=14)
            ttk.Label(self.panel, text="Regla de satisfacción", style="Seccion.TLabel").pack(anchor="w")
            ttk.Label(self.panel, text="1 punto si recibe su turno preferido.\n0 puntos si recibe otro turno.\nCada turno se utiliza exactamente una vez.\n\nAna y María comparten preferencia por Mañana. Solo una puede recibirlo: el máximo posible es 3 de 4.", wraplength=280).pack(anchor="w", pady=8)

            self.pestanas = ttk.Notebook(principal)
            self.pestanas.grid(row=1, column=1, sticky="nsew")
            solucion = ttk.Frame(self.pestanas, padding=12)
            self.pestanas.add(solucion, text="Resultado y gráfica")
            solucion.columnconfigure(0, weight=1)
            solucion.rowconfigure(4, weight=1)
            ttk.Label(solucion, textvariable=self.resumen, style="Resultado.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
            opciones = ttk.Frame(solucion)
            opciones.grid(row=1, column=0, sticky="ew", pady=(0, 8))
            ttk.Label(opciones, text="Mostrar:").pack(side="left", padx=(0, 8))
            self.selector_solucion = ttk.Combobox(opciones, textvariable=self.opcion, state="readonly", width=29)
            self.selector_solucion.pack(side="left")
            self.selector_solucion.bind("<<ComboboxSelected>>", lambda _: self.mostrar())
            tabla_marco = ttk.Frame(solucion)
            tabla_marco.grid(row=2, column=0, sticky="ew")
            self.tabla_resultado = self.tabla(tabla_marco, (("empleado", "Empleado", 125), ("preferencia", "Prefiere", 130),
                                                         ("turno", "Turno asignado", 145), ("cumple", "¿Cumple?", 110)), 4)
            ttk.Label(solucion, text="Dos soluciones óptimas: Ana o María recibe Mañana; la otra recibe Mixto.\nComprobación independiente de las 24 asignaciones posibles.", wraplength=750).grid(row=3, column=0, sticky="w", pady=8)
            self.figura = Figure(figsize=(9, 4), dpi=100, layout="constrained")
            self.lienzo = FigureCanvasTkAgg(self.figura, master=solucion)
            self.lienzo.get_tk_widget().grid(row=4, column=0, sticky="nsew")
            self.lienzo.get_tk_widget().bind("<Map>", self.ajustar_lienzo, add="+")

            recorrido = ttk.Frame(self.pestanas, padding=14)
            self.pestanas.add(recorrido, text="Intercambios paso a paso")
            ttk.Label(recorrido, text="Solo se aceptan intercambios que aumentan la puntuación.", style="Seccion.TLabel").pack(anchor="w", pady=(0, 10))
            columnas = (("paso", "Paso", 50), *((n, n, 95) for n in EMPLEADOS),
                        ("puntos", "Puntos / 4", 85), ("cambio", "Intercambio", 170))
            self.tabla_pasos = self.tabla(recorrido, columnas, 9, desplazamiento=True)
            ttk.Label(recorrido, text="Cada estado tiene seis vecinos: uno por cada pareja de empleados.\nSe revisan todos y se elige el que más mejora. Si ninguno mejora, la búsqueda termina.\n\nLa revisión de las 24 asignaciones se calcula aparte y no guía los pasos de Hill Climbing.\nEn este ejercicio, ambas asignaciones óptimas valen lo mismo; no se estableció una preferencia entre empleados.", wraplength=720).pack(anchor="w", pady=16)
            pie = ttk.Frame(principal)
            pie.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
            pie.columnconfigure(0, weight=1)
            self.pie = ttk.Label(pie, textvariable=self.estado, wraplength=810)
            self.pie.grid(row=0, column=0, sticky="w", padx=(0, 12))
            self.boton_guardar = ttk.Button(pie, text="Guardar gráfica PNG", command=self.guardar)
            self.boton_guardar.grid(row=0, column=1, sticky="e")
            for variable in self.entradas:
                variable.trace_add("write", self.marcar_pendiente)
            self.calcular()

        def ajustar_lienzo(self, evento):
            widget = evento.widget
            widget.after_idle(lambda: widget.event_generate("<Configure>", width=widget.winfo_width(), height=widget.winfo_height()))

        def tabla(self, panel, columnas, alto, desplazamiento=False):
            marco = ttk.Frame(panel)
            marco.pack(fill="x")
            marco.columnconfigure(0, weight=1)
            tabla = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings", height=alto)
            for clave, titulo, ancho in columnas:
                tabla.heading(clave, text=titulo)
                tabla.column(clave, width=ancho, minwidth=ancho, stretch=not desplazamiento, anchor="center")
            tabla.grid(row=0, column=0, sticky="ew")
            if desplazamiento:
                barra = ttk.Scrollbar(marco, orient="horizontal", command=tabla.xview)
                tabla.configure(xscrollcommand=barra.set)
                barra.grid(row=1, column=0, sticky="ew")
            return tabla

        def marcar_pendiente(self, *_):
            self.pendiente = True
            self.boton_guardar.configure(state="disabled")
            self.estado.set("Inicio modificado. Los resultados conservan la última búsqueda; pulsa Asignar turnos para actualizar.")

        def intercambiar_inicio(self, indice):
            nuevo = self.entradas[indice].get()
            ocupante = self.inicio_actual.index(nuevo)
            anterior = self.inicio_actual[indice]
            self.entradas[ocupante].set(anterior)
            self.inicio_actual = tuple(v.get() for v in self.entradas)

        def calcular(self):
            try:
                inicio = validar_asignacion(v.get() for v in self.entradas)
                resultado = hill_climbing(inicio)
            except ValueError as error:
                self.marcar_pendiente()
                self.estado.set(str(error) + " Los resultados anteriores no se actualizaron.")
                return False
            self.inicio_actual = inicio
            self.resultado = resultado
            self.verificacion = verificar_optimas()
            self.opciones = [resultado.final.asignacion, *self.verificacion.asignaciones]
            etiquetas = ["Resultado de Hill Climbing", *[f"Asignación óptima {i}" for i in range(1, len(self.opciones))]]
            self.selector_solucion.configure(values=etiquetas)
            self.selector_solucion.current(0)
            self.tabla_pasos.delete(*self.tabla_pasos.get_children())
            for i, paso in enumerate(resultado.pasos):
                intercambio = "Inicio" if paso.intercambio is None else " / ".join(paso.intercambio)
                self.tabla_pasos.insert("", "end", values=(i, *paso.asignacion, paso.satisfaccion, intercambio))
            self.pendiente = False
            self.boton_guardar.configure(state="normal")
            self.mostrar()
            self.estado.set(f"Búsqueda terminada: {len(resultado.pasos) - 1} intercambios aceptados. Máximo comprobado: 3 de 4 preferencias (75 %).")
            return True

        def mostrar(self):
            self.mostrada = self.opciones[self.selector_solucion.current()]
            puntos = puntuar(self.mostrada)
            self.resumen.set(f"{puntos} de 4 preferencias cumplidas · {puntos / 4:.0%}")
            self.tabla_resultado.delete(*self.tabla_resultado.get_children())
            for empleado, preferencia, turno in zip(EMPLEADOS, PREFERENCIAS, self.mostrada):
                self.tabla_resultado.insert("", "end", values=(empleado, preferencia, turno, "Sí" if preferencia == turno else "No"))
            dibujar(self.figura, self.mostrada, self.resultado, self.verificacion)
            self.lienzo.draw_idle()

        def restablecer(self):
            for variable, turno in zip(self.entradas, INICIO):
                variable.set(turno)
            self.calcular()

        def guardar(self):
            if self.pendiente:
                self.estado.set("Calcula los cambios pendientes antes de exportar la gráfica.")
                return
            destino = filedialog.asksaveasfilename(parent=raiz, title="Guardar gráfica de turnos", initialfile="Asignacion_turnos.png",
                defaultextension=".png", filetypes=[("Imagen PNG", "*.png")])
            if not destino:
                return
            try:
                ruta = guardar_png(destino, self.mostrada, self.resultado, self.verificacion)
            except (OSError, ValueError) as error:
                self.estado.set(f"No se pudo guardar la imagen: {error}")
                return
            self.estado.set(f"Gráfica guardada: {ruta}")

    return Aplicacion()


def main():
    parser = argparse.ArgumentParser(description="Asignación de cuatro empleados a cuatro turnos.")
    parser.add_argument("--inicio", nargs=4, metavar="TURNO", default=INICIO, help="turnos iniciales de Ana, Luis, Carlos y María, en ese orden")
    parser.add_argument("--terminal", action="store_true", help="calcular sin dependencias gráficas")
    parser.add_argument("--sin-ventana", action="store_true", help="calcular y guardar PNG sin abrir la interfaz")
    parser.add_argument("--salida", type=Path, help="ruta PNG; activa la exportación sin ventana")
    args = parser.parse_args()
    try:
        inicio = validar_asignacion(args.inicio)
        resultado, verificacion = hill_climbing(inicio), verificar_optimas()
        if args.terminal or args.sin_ventana or args.salida:
            imprimir(resultado, verificacion)
            if args.sin_ventana or args.salida:
                from graficas import guardar_png
                print("Gráfica guardada:", guardar_png(args.salida or SALIDA, resultado.final.asignacion, resultado, verificacion))
            return
        import tkinter as tk
        try:
            raiz = tk.Tk()
        except tk.TclError:
            parser.exit(1, "No se pudo abrir la ventana. Revisa WSLg o usa --terminal o --sin-ventana.\n")
        try:
            crear_interfaz(raiz, inicio)
        except ImportError:
            raiz.destroy()
            raise
        raiz.mainloop()
    except ImportError as error:
        ayuda = ("Instala Tkinter para tu Python (en Ubuntu: sudo apt install python3-tk)."
                 if (error.name or "") in ("tkinter", "_tkinter") else "Instala Matplotlib con el requirements.txt de esta práctica.")
        parser.exit(1, ayuda + " También puedes usar --terminal.\n")
    except (ValueError, OSError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
