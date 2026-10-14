"""Práctica 16: puntos editables, distancias Manhattan/Euclidiana y gráficas."""
import argparse
from pathlib import Path
from textwrap import fill

from distancias import PUNTO_A, PUNTO_B, calcular_distancias, conclusion, numero, texto_punto


ORDENES = {"Primero X, después Y": "xy", "Primero Y, después X": "yx"}
SALIDA = Path(__file__).resolve().parent / "salidas" / "Comparacion_distancias.png"
COMPARACION = (
    ("Concepto", "Suma de los desplazamientos por los ejes X e Y.", "Longitud del segmento recto entre A y B."),
    ("Movimiento", "Horizontal y vertical; no usa diagonales.", "Directo, en cualquier dirección."),
    ("Fórmula", "|xB − xA| + |yB − yA|", "√((xB − xA)² + (yB − yA)²)"),
    ("Geometría", "Los puntos a igual distancia forman un rombo (diamante).", "Los puntos a igual distancia forman una circunferencia."),
    ("Fundamento", "Suma de longitudes por coordenadas; norma L1.", "Teorema de Pitágoras; norma L2."),
    ("Uso como h(n)", "Cuadrícula con movimientos por ejes y costo unitario.", "Estimación en línea recta si el costo respeta la distancia geométrica."),
    ("Relación", "Es mayor o igual que la distancia Euclidiana.", "Es menor o igual que la distancia Manhattan."),
)


def leer_numero(texto, campo):
    try:
        return float(str(texto).strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"Escribe un número en {campo}; por ejemplo, 1, 2.5 o -3.") from None


def imprimir_resultado(m):
    print(f"\nPRÁCTICA 16 · A = {texto_punto(m.a)} · B = {texto_punto(m.b)}")
    print(f"Δx = |({numero(m.b[0])}) - ({numero(m.a[0])})| = {numero(m.dx)}")
    print(f"Δy = |({numero(m.b[1])}) - ({numero(m.a[1])})| = {numero(m.dy)}")
    print(f"Manhattan = |xB - xA| + |yB - yA| = {numero(m.dx)} + {numero(m.dy)} = {numero(m.manhattan)}")
    print(f"Euclidiana = √(Δx² + Δy²) = √({numero(m.dx)}² + {numero(m.dy)}²) = {numero(m.euclidiana)}")
    print(conclusion(m))
    print("Resultados en unidades del plano, sin obstáculos ni costos adicionales.")


def crear_interfaz(raiz, a=PUNTO_A, b=PUNTO_B, orden="xy"):
    import tkinter as tk
    from tkinter import filedialog, ttk
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from grafica_distancias import dibujar_comparacion, guardar_png, validar_rango_grafico

    class Aplicacion:
        def __init__(self):
            self.medicion = None
            self.pendiente = False
            self.coordenadas = {clave: tk.StringVar(value=str(valor))
                               for clave, valor in zip(("A.X", "A.Y", "B.X", "B.Y"), (*a, *b))}
            self.orden = tk.StringVar(value=next(k for k, v in ORDENES.items() if v == orden))
            self.estado = tk.StringVar()
            self.valor_m, self.valor_e = tk.StringVar(), tk.StringVar()
            self.desglose = tk.StringVar()
            self.figura = Figure(figsize=(8.5, 7), dpi=100, layout="constrained")
            raiz.title("Práctica 16 · Distancias Manhattan y Euclidiana")
            raiz.geometry("1230x860")
            raiz.minsize(1070, 780)
            estilo = ttk.Style(raiz)
            estilo.theme_use("clam")
            estilo.configure("TFrame", background="#f5f8fc")
            estilo.configure("TLabel", background="#f5f8fc", foreground="#20354e", font=("DejaVu Sans", 10))
            estilo.configure("Titulo.TLabel", font=("DejaVu Sans", 23, "bold"))
            estilo.configure("Subtitulo.TLabel", font=("DejaVu Sans", 12, "bold"))
            estilo.configure("Manhattan.TLabel", foreground="#b15b1e", font=("DejaVu Sans", 23, "bold"))
            estilo.configure("Euclidiana.TLabel", foreground="#236db5", font=("DejaVu Sans", 23, "bold"))
            estilo.configure("TButton", padding=(10, 8), font=("DejaVu Sans", 10))
            estilo.configure("Comparacion.Treeview", rowheight=92, font=("DejaVu Sans", 10))
            principal = ttk.Frame(raiz, padding=20)
            principal.pack(fill="both", expand=True)
            principal.columnconfigure(0, weight=1)
            principal.rowconfigure(1, weight=1)
            cabecera = ttk.Frame(principal)
            cabecera.grid(row=0, column=0, sticky="ew", pady=(0, 16))
            ttk.Label(cabecera, text="UTVT · FUNDAMENTOS DE IA · PRÁCTICA 16").pack(anchor="w")
            ttk.Label(cabecera, text="Dos formas de medir la distancia", style="Titulo.TLabel").pack(anchor="w", pady=(4, 6))
            ttk.Label(cabecera, text="Manhattan: recorrido por ejes   ·   Euclidiana: línea recta   ·   Misma escala en X e Y").pack(anchor="w")
            cuerpo = ttk.Frame(principal)
            cuerpo.grid(row=1, column=0, sticky="nsew")
            cuerpo.columnconfigure(0, minsize=300)
            cuerpo.columnconfigure(1, weight=1)
            cuerpo.rowconfigure(0, weight=1)
            panel = ttk.Frame(cuerpo, padding=(0, 0, 20, 0))
            panel.grid(row=0, column=0, sticky="nsw")
            ttk.Label(panel, text="Puntos del plano", style="Subtitulo.TLabel").pack(anchor="w", pady=(0, 10))
            campos = ttk.Frame(panel)
            campos.pack(anchor="w")
            ttk.Label(campos, text="X").grid(row=0, column=1, sticky="w")
            ttk.Label(campos, text="Y").grid(row=0, column=2, sticky="w")
            self.entradas = {}
            for fila, nombre in enumerate(("A", "B"), 1):
                ttk.Label(campos, text=nombre).grid(row=fila, column=0, padx=(0, 12))
                for columna, eje in enumerate(("X", "Y"), 1):
                    clave = nombre + "." + eje
                    entrada = ttk.Entry(campos, textvariable=self.coordenadas[clave], width=11)
                    entrada.grid(row=fila, column=columna, padx=(0, 10), pady=5)
                    entrada.bind("<Return>", lambda evento: self.calcular())
                    self.entradas[clave] = entrada
            ttk.Label(panel, text="Admite negativos y decimales con punto o coma.\nVisor: de -1000000 a 1000000 por coordenada.", wraplength=285).pack(anchor="w", pady=(5, 12))
            ttk.Label(panel, text="Recorrido Manhattan").pack(anchor="w", pady=(0, 5))
            self.selector = ttk.Combobox(panel, textvariable=self.orden, values=list(ORDENES), state="readonly", width=27)
            self.selector.pack(anchor="w")
            self.selector.bind("<<ComboboxSelected>>", lambda evento: self.calcular())
            botones = ttk.Frame(panel)
            botones.pack(fill="x", pady=12)
            self.boton_calcular = ttk.Button(botones, text="Calcular", command=self.calcular)
            self.boton_calcular.pack(side="left", padx=(0, 8))
            ttk.Button(botones, text="Restablecer", command=self.restablecer).pack(side="left")
            self.boton_guardar = ttk.Button(panel, text="Guardar gráfica PNG", command=self.guardar)
            self.boton_guardar.pack(anchor="w", pady=(0, 14))
            ttk.Separator(panel).pack(fill="x", pady=(0, 12))
            ttk.Label(panel, text="DISTANCIA MANHATTAN · L1").pack(anchor="w")
            ttk.Label(panel, textvariable=self.valor_m, style="Manhattan.TLabel").pack(anchor="w", pady=(3, 10))
            ttk.Label(panel, text="DISTANCIA EUCLIDIANA · L2").pack(anchor="w")
            ttk.Label(panel, textvariable=self.valor_e, style="Euclidiana.TLabel").pack(anchor="w", pady=(3, 12))
            ttk.Label(panel, textvariable=self.desglose, wraplength=285).pack(anchor="w")

            self.pestanas = ttk.Notebook(cuerpo)
            self.pestanas.grid(row=0, column=1, sticky="nsew")
            marco_grafica = ttk.Frame(self.pestanas)
            self.pestanas.add(marco_grafica, text="Gráfica comparativa")
            self.lienzo = FigureCanvasTkAgg(self.figura, master=marco_grafica)
            self.lienzo.get_tk_widget().pack(fill="both", expand=True)
            conceptos = ttk.Frame(self.pestanas, padding=16)
            self.pestanas.add(conceptos, text="Tabla de diferencias")
            conceptos.columnconfigure(0, weight=1)
            conceptos.rowconfigure(1, weight=1)
            ttk.Label(conceptos, text="Manhattan y Euclidiana", style="Subtitulo.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))
            # Tres columnas y desplazamiento para conservar la tabla completa.
            tabla = ttk.Frame(conceptos)
            tabla.grid(row=1, column=0, sticky="nsew")
            tabla.columnconfigure(0, weight=1)
            tabla.rowconfigure(0, weight=1)
            self.tabla = ttk.Treeview(tabla, columns=("concepto", "manhattan", "euclidiana"),
                                     show="headings", style="Comparacion.Treeview", height=5)
            for clave, titulo, ancho in (("concepto", "Concepto", 110), ("manhattan", "Manhattan", 250), ("euclidiana", "Euclidiana", 250)):
                self.tabla.heading(clave, text=titulo)
                self.tabla.column(clave, width=ancho, minwidth=ancho, anchor="w", stretch=clave != "concepto")
            barra = ttk.Scrollbar(tabla, command=self.tabla.yview)
            horizontal = ttk.Scrollbar(tabla, orient="horizontal", command=self.tabla.xview)
            self.tabla.configure(yscrollcommand=barra.set, xscrollcommand=horizontal.set)
            self.tabla.grid(row=0, column=0, sticky="nsew")
            barra.grid(row=0, column=1, sticky="ns")
            horizontal.grid(row=1, column=0, sticky="ew")
            for concepto, manhattan, euclidiana in COMPARACION:
                self.tabla.insert("", "end", values=(fill(concepto, 13), fill(manhattan, 29), fill(euclidiana, 29)))
            ttk.Label(conceptos, text="El rombo y la circunferencia describen puntos a igual distancia de un centro, no las rutas entre A y B.\nLas distancias no incorporan obstáculos ni costos adicionales de un mapa.", wraplength=600).grid(row=2, column=0, sticky="w", pady=(12, 0))
            self.pie = ttk.Label(principal, textvariable=self.estado, wraplength=1010)
            self.pie.grid(row=2, column=0, sticky="ew", pady=(12, 0))
            for variable in self.coordenadas.values():
                variable.trace_add("write", self.marcar_pendiente)
            self.calcular()

        def marcar_pendiente(self, *_):
            self.pendiente = True
            self.boton_guardar.configure(state="disabled")
            self.estado.set("Hay cambios sin calcular. La gráfica conserva los últimos puntos válidos; pulsa Calcular.")

        def calcular(self):
            try:
                valores = {clave: leer_numero(var.get(), clave) for clave, var in self.coordenadas.items()}
                medicion = calcular_distancias((valores['A.X'], valores['A.Y']), (valores['B.X'], valores['B.Y']))
                validar_rango_grafico(medicion)
            except ValueError as error:
                self.estado.set(str(error) + " La gráfica anterior no se actualizó.")
                self.boton_guardar.configure(state="disabled")
                return False
            self.medicion = medicion
            dibujar_comparacion(self.figura, medicion, ORDENES[self.orden.get()])
            self.lienzo.draw_idle()
            self.valor_m.set(numero(medicion.manhattan) + " unidades")
            self.valor_e.set(numero(medicion.euclidiana) + " unidades")
            self.desglose.set(f"Δx = {numero(medicion.dx)} · Δy = {numero(medicion.dy)}\n\nManhattan = Δx + Δy\n= {numero(medicion.dx)} + {numero(medicion.dy)} = {numero(medicion.manhattan)}\n\nEuclidiana = √(Δx² + Δy²)\n= √({numero(medicion.dx)}² + {numero(medicion.dy)}²) = {numero(medicion.euclidiana)}")
            self.estado.set(conclusion(medicion) + " Resultados en unidades del plano.")
            self.pendiente = False
            self.boton_guardar.configure(state="normal")
            return True

        def restablecer(self):
            for clave, valor in zip(self.coordenadas, (*PUNTO_A, *PUNTO_B)):
                self.coordenadas[clave].set(numero(valor))
            self.orden.set(next(iter(ORDENES)))
            self.calcular()

        def guardar(self):
            if self.pendiente and not self.calcular():
                return
            destino = filedialog.asksaveasfilename(parent=raiz, title="Guardar comparación de distancias",
                defaultextension=".png", initialfile="Comparacion_distancias.png", filetypes=[("Imagen PNG", "*.png")])
            if not destino:
                return
            try:
                ruta = guardar_png(self.medicion, destino, ORDENES[self.orden.get()])
            except (OSError, ValueError) as error:
                self.estado.set(f"No se pudo guardar la gráfica: {error}")
                return
            self.estado.set(f"Gráfica guardada: {ruta}")

    return Aplicacion()


def main():
    parser = argparse.ArgumentParser(description="Distancias Manhattan y Euclidiana entre A y B.")
    parser.add_argument("--a", nargs=2, metavar=("X", "Y"), default=PUNTO_A, help="coordenadas del punto A")
    parser.add_argument("--b", nargs=2, metavar=("X", "Y"), default=PUNTO_B, help="coordenadas del punto B")
    parser.add_argument("--orden", choices=("xy", "yx"), default="xy", help="orden del recorrido Manhattan")
    parser.add_argument("--terminal", action="store_true", help="solo calcular; no necesita Matplotlib ni Tkinter")
    parser.add_argument("--sin-ventana", action="store_true", help="calcular y guardar un PNG sin interfaz")
    parser.add_argument("--salida", type=Path, help="ruta PNG; activa la exportación sin ventana")
    args = parser.parse_args()
    try:
        a = tuple(leer_numero(v, 'A.' + eje) for eje, v in zip(('X', 'Y'), args.a))
        b = tuple(leer_numero(v, 'B.' + eje) for eje, v in zip(('X', 'Y'), args.b))
        medicion = calcular_distancias(a, b)
        if args.terminal or args.sin_ventana or args.salida:
            imprimir_resultado(medicion)
            if args.sin_ventana or args.salida:
                from grafica_distancias import guardar_png
                ruta = guardar_png(medicion, args.salida or SALIDA, args.orden)
                print("Gráfica guardada:", ruta)
            return
        import tkinter as tk
        from grafica_distancias import validar_rango_grafico
        validar_rango_grafico(medicion)
        try:
            raiz = tk.Tk()
        except tk.TclError:
            parser.exit(1, "No se pudo abrir la ventana. Revisa WSLg o usa --sin-ventana o --terminal.\n")
        try:
            crear_interfaz(raiz, a, b, args.orden)
        except ImportError:
            raiz.destroy()
            raise
        raiz.mainloop()
    except ImportError as error:
        ayuda = "Instala Tkinter para tu Python (en Ubuntu: sudo apt install python3-tk)." if (error.name or "") in ("tkinter", "_tkinter") else "Instala Matplotlib con el requirements.txt de esta práctica."
        parser.exit(1, ayuda + " También puedes usar --terminal.\n")
    except (ValueError, OSError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
