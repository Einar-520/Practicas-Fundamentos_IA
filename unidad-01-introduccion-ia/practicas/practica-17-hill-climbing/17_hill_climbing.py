"""Práctica 17: Hill Climbing en una lista y en una selección de productos."""
import argparse
from pathlib import Path

from hill_climbing import (
    LISTA, PRODUCTOS, PRESUPUESTO, leer_lista, nombres, numero,
    subir_lista, subir_productos, verificar_optimo,
)


SALIDA = Path(__file__).resolve().parent / "salidas" / "Hill_Climbing.png"


def imprimir_resultados(lista, productos, exacta, presupuesto):
    print("\nPRÁCTICA 17 · HILL CLIMBING")
    print("Lista:", ", ".join(map(numero, lista.valores)))
    print("Recorrido:", " -> ".join(map(numero, lista.recorrido)))
    print(f"Parada: posición {lista.indices[-1] + 1}, valor {numero(lista.valor_final)}.")
    print("Ningún vecino adyacente tiene un valor mayor. Movimientos:", len(lista.indices) - 1)
    print(f"\nProductos · Presupuesto ${presupuesto:,} · Una unidad de cada producto como máximo")
    for i, paso in enumerate(productos.pasos):
        print(f"Paso {i}: {nombres(paso)} | Costo ${paso.costo:,} | Beneficio {paso.beneficio}")
    print("Parada: ningún vecino factible mejora el beneficio.")
    print(f"Disponible: ${presupuesto - productos.final.costo:,}")
    print(f"\nComprobación independiente: {exacta.combinaciones} combinaciones; {exacta.factibles} factibles.")
    print(f"Beneficio global máximo: {exacta.beneficio} unidades. Mejores selecciones:")
    for solucion in exacta.soluciones:
        print(f"  {nombres(solucion)} | Costo ${solucion.costo:,} | Beneficio {solucion.beneficio}")
    if productos.final.beneficio == exacta.beneficio:
        print("Hill Climbing coincide con el óptimo global en esta ejecución.")
    else:
        print(f"Hill Climbing quedó en un máximo local: faltan {exacta.beneficio - productos.final.beneficio} unidades de beneficio.")


def crear_interfaz(raiz, valores=LISTA, inicio=0, presupuesto=PRESUPUESTO, seleccion=()):
    import tkinter as tk
    from tkinter import ttk, filedialog
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from graficas import actualizar_lista, actualizar_productos, guardar_png

    class Aplicacion:
        def __init__(self):
            self.texto_lista = tk.StringVar(value=", ".join(map(str, valores)))
            self.inicio = tk.StringVar(value=str(inicio + 1))
            self.presupuesto = tk.StringVar(value=str(presupuesto))
            self.elegidos = {p.nombre: tk.BooleanVar(value=p.nombre in seleccion) for p in PRODUCTOS}
            self.resumen_lista, self.resumen_productos, self.verificacion = (tk.StringVar() for _ in range(3))
            self.estado = tk.StringVar()
            self.pendientes = {"lista": False, "productos": False}
            raiz.title("Práctica 17 · Hill Climbing")
            raiz.geometry("1360x920")
            raiz.minsize(1180, 850)
            estilo = ttk.Style(raiz)
            estilo.theme_use("clam")
            estilo.configure("TFrame", background="#f5f8fc")
            estilo.configure("TLabel", background="#f5f8fc", foreground="#20354e", font=("DejaVu Sans", 10))
            estilo.configure("Titulo.TLabel", font=("DejaVu Sans", 24, "bold"))
            estilo.configure("Seccion.TLabel", font=("DejaVu Sans", 12, "bold"))
            estilo.configure("Resultado.TLabel", foreground="#126a59", font=("DejaVu Sans", 12, "bold"))
            estilo.configure("TButton", padding=(10, 7), font=("DejaVu Sans", 10))
            estilo.configure("TCheckbutton", background="#f5f8fc")
            estilo.configure("Treeview", rowheight=25, font=("DejaVu Sans", 10))
            principal = ttk.Frame(raiz, padding=20)
            principal.pack(fill="both", expand=True)
            principal.columnconfigure(0, weight=1)
            principal.rowconfigure(1, weight=1)
            cabecera = ttk.Frame(principal)
            cabecera.grid(row=0, column=0, sticky="ew", pady=(0, 12))
            ttk.Label(cabecera, text="UTVT · FUNDAMENTOS DE IA · PRÁCTICA 17").pack(anchor="w")
            ttk.Label(cabecera, text="Hill Climbing: mejorar paso a paso", style="Titulo.TLabel").pack(anchor="w", pady=5)
            ttk.Label(cabecera, text="Elegir el mejor vecino · Aceptar solo mejoras · Detenerse si ningún vecino mejora").pack(anchor="w")
            self.pestanas = ttk.Notebook(principal)
            self.pestanas.grid(row=1, column=0, sticky="nsew")
            self.paneles, self.figuras, self.lienzos = {}, {}, {}
            for clave, titulo in (("lista", "1 · Recorrido de la lista"), ("productos", "2 · Presupuesto y productos")):
                pestana = ttk.Frame(self.pestanas, padding=14)
                self.pestanas.add(pestana, text=titulo)
                pestana.columnconfigure(1, weight=1)
                pestana.rowconfigure(0, weight=1)
                panel = ttk.Frame(pestana, padding=(0, 0, 18, 0))
                panel.grid(row=0, column=0, sticky="nsw")
                self.paneles[clave] = panel
                figura = Figure(figsize=(8, 7), dpi=100, layout="constrained")
                lienzo = FigureCanvasTkAgg(figura, master=pestana)
                lienzo.get_tk_widget().grid(row=0, column=1, sticky="nsew")
                # Matplotlib puede ajustar los DPI al mapear una pestaña. Una
                # nueva medición evita recortes si su tamaño visible no cambió.
                lienzo.get_tk_widget().bind("<Map>", self.ajustar_lienzo, add="+")
                self.figuras[clave], self.lienzos[clave] = figura, lienzo

            panel = self.paneles["lista"]
            ttk.Label(panel, text="Datos de la lista", style="Seccion.TLabel").pack(anchor="w")
            self.entrada_lista = ttk.Entry(panel, textvariable=self.texto_lista, width=37)
            self.entrada_lista.pack(fill="x", pady=(8, 4))
            ttk.Label(panel, text="Separa los valores con comas. Usa punto decimal.\nPuedes escribir de 1 a 40 valores.", wraplength=350).pack(anchor="w")
            inicio_fila = ttk.Frame(panel)
            inicio_fila.pack(fill="x", pady=12)
            ttk.Label(inicio_fila, text="Posición inicial (desde 1):").pack(side="left")
            self.selector_inicio = ttk.Spinbox(inicio_fila, from_=1, to=40, textvariable=self.inicio, width=5)
            self.selector_inicio.pack(side="left", padx=8)
            self.botones(panel, self.calcular_lista, self.restablecer_lista)
            ttk.Separator(panel).pack(fill="x", pady=12)
            ttk.Label(panel, textvariable=self.resumen_lista, style="Resultado.TLabel", wraplength=350).pack(anchor="w")
            ttk.Label(panel, text="Recorrido aceptado", style="Seccion.TLabel").pack(anchor="w", pady=(16, 8))
            self.tabla_lista = self.tabla(panel, (("paso", "Paso", 65), ("posicion", "Posición", 90), ("valor", "Valor", 150)), 7)
            ttk.Label(panel, text="Se comparan los vecinos izquierdo y derecho.\nUn valor igual no permite avanzar.\n\nPrueba 2, 5, 4, 12: desde 2 se detiene en 5, aunque existe un 12 más adelante.", wraplength=350).pack(anchor="w", pady=14)

            panel = self.paneles["productos"]
            ttk.Label(panel, text="Presupuesto en pesos enteros", style="Seccion.TLabel").pack(anchor="w")
            self.entrada_presupuesto = ttk.Entry(panel, textvariable=self.presupuesto, width=16)
            self.entrada_presupuesto.pack(anchor="w", pady=(7, 8))
            ttk.Label(panel, text="Selección inicial · Deja vacío para empezar de cero.", wraplength=350).pack(anchor="w")
            catalogo = ttk.Frame(panel)
            catalogo.pack(fill="x", pady=6)
            for columna, titulo in enumerate(("Producto", "Costo ($)", "Beneficio")):
                ttk.Label(catalogo, text=titulo).grid(row=0, column=columna, sticky="w", padx=(0, 20), pady=3)
            self.casillas = {}
            for fila, producto in enumerate(PRODUCTOS, 1):
                casilla = ttk.Checkbutton(catalogo, text=producto.nombre, variable=self.elegidos[producto.nombre])
                casilla.grid(row=fila, column=0, sticky="w")
                self.casillas[producto.nombre] = casilla
                ttk.Label(catalogo, text=str(producto.costo)).grid(row=fila, column=1, sticky="w")
                ttk.Label(catalogo, text=str(producto.beneficio)).grid(row=fila, column=2, sticky="w")
            self.botones(panel, self.calcular_productos, self.restablecer_productos)
            ttk.Label(panel, textvariable=self.resumen_productos, style="Resultado.TLabel", wraplength=350).pack(anchor="w", pady=(10, 8))
            ttk.Label(panel, textvariable=self.verificacion, wraplength=350).pack(anchor="w")
            ttk.Label(panel, text="Pasos de Hill Climbing", style="Seccion.TLabel").pack(anchor="w", pady=(12, 6))
            self.tabla_productos = self.tabla(panel, (("paso", "Paso", 45), ("productos", "Productos", 110),
                                                     ("costo", "Costo ($)", 80), ("beneficio", "Beneficio", 80)), 4)
            ttk.Label(panel, text="Vecinos: agregar, retirar o intercambiar un producto. Máximo una unidad de cada uno.\nLa comprobación global se calcula por separado.", wraplength=350).pack(anchor="w", pady=(10, 0))
            pie = ttk.Frame(principal)
            pie.grid(row=2, column=0, sticky="ew", pady=(12, 0))
            pie.columnconfigure(0, weight=1)
            self.pie = ttk.Label(pie, textvariable=self.estado, wraplength=810)
            self.pie.grid(row=0, column=0, sticky="w", padx=(0, 10))
            self.boton_guardar = ttk.Button(pie, text="Guardar ambas gráficas PNG", command=self.guardar)
            self.boton_guardar.grid(row=0, column=1, sticky="e")
            for variable in (self.texto_lista, self.inicio):
                variable.trace_add("write", lambda *_: self.marcar_pendiente("lista"))
            for variable in (self.presupuesto, *self.elegidos.values()):
                variable.trace_add("write", lambda *_: self.marcar_pendiente("productos"))
            self.entrada_lista.bind("<Return>", lambda _: self.calcular_lista())
            self.entrada_presupuesto.bind("<Return>", lambda _: self.calcular_productos())
            self.calcular_lista()
            self.calcular_productos()

        def ajustar_lienzo(self, evento):
            widget = evento.widget
            widget.after_idle(lambda: widget.event_generate("<Configure>",
                width=widget.winfo_width(), height=widget.winfo_height()))

        def botones(self, panel, calcular, restablecer):
            fila = ttk.Frame(panel)
            fila.pack(fill="x", pady=5)
            ttk.Button(fila, text="Buscar", command=calcular).pack(side="left", padx=(0, 8))
            ttk.Button(fila, text="Restablecer", command=restablecer).pack(side="left")

        def tabla(self, panel, columnas, alto):
            marco = ttk.Frame(panel)
            marco.pack(fill="x")
            tabla = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings", height=alto)
            for clave, titulo, ancho in columnas:
                tabla.heading(clave, text=titulo)
                tabla.column(clave, width=ancho, minwidth=ancho, stretch=False, anchor="center")
            barra = ttk.Scrollbar(marco, command=tabla.yview)
            tabla.configure(yscrollcommand=barra.set)
            tabla.pack(side="left", fill="x", expand=True)
            barra.pack(side="right", fill="y")
            return tabla

        def marcar_pendiente(self, clave):
            self.pendientes[clave] = True
            self.boton_guardar.configure(state="disabled")
            self.estado.set("Hay cambios sin calcular. Las gráficas y los resultados conservan la última búsqueda; pulsa Buscar en la pestaña modificada.")

        def listo(self, clave):
            self.pendientes[clave] = False
            if any(self.pendientes.values()):
                self.estado.set("Resultado actualizado. Aún hay cambios sin calcular en la otra pestaña.")
            else:
                self.boton_guardar.configure(state="normal")
                self.estado.set("Búsquedas terminadas. Hill Climbing se detiene cuando ningún vecino ofrece una mejora estricta.")

        def error(self, clave, error):
            self.pendientes[clave] = True
            self.boton_guardar.configure(state="disabled")
            self.estado.set(str(error) + " Los resultados anteriores no se actualizaron.")
            return False

        def calcular_lista(self):
            try:
                valores = leer_lista(self.texto_lista.get())
                try:
                    posicion = int(self.inicio.get())
                except ValueError:
                    raise ValueError("La posición inicial debe ser un número entero.") from None
                resultado = subir_lista(valores, posicion - 1)
            except ValueError as error:
                return self.error("lista", error)
            self.lista = resultado
            self.selector_inicio.configure(to=len(valores))
            actualizar_lista(self.figuras["lista"], resultado)
            self.lienzos["lista"].draw_idle()
            global_lista = max(resultado.valores)
            comprobacion = ("Coincide con el máximo de la lista." if resultado.valor_final == global_lista
                            else f"Máximo local. El máximo global es {numero(global_lista)}.")
            self.resumen_lista.set(f"Parada: {numero(resultado.valor_final)} · Posición {resultado.indices[-1] + 1}\n"
                                   f"Movimientos: {len(resultado.indices) - 1}\n{comprobacion}")
            self.tabla_lista.delete(*self.tabla_lista.get_children())
            for paso, indice in enumerate(resultado.indices):
                self.tabla_lista.insert("", "end", values=(paso, indice + 1, numero(resultado.valores[indice])))
            self.listo("lista")
            return True

        def calcular_productos(self):
            try:
                try:
                    presupuesto = int(self.presupuesto.get())
                except ValueError:
                    raise ValueError("Escribe un presupuesto entero, por ejemplo 1000, sin símbolo $ ni separadores.") from None
                seleccion = tuple(n for n, var in self.elegidos.items() if var.get())
                resultado = subir_productos(PRODUCTOS, presupuesto, seleccion)
                exacta = verificar_optimo(PRODUCTOS, presupuesto)
            except ValueError as error:
                return self.error("productos", error)
            self.productos, self.exacta, self.presupuesto_calculado = resultado, exacta, presupuesto
            actualizar_productos(self.figuras["productos"], resultado, exacta, presupuesto)
            self.lienzos["productos"].draw_idle()
            final = resultado.final
            self.resumen_productos.set(f"Hill Climbing: {nombres(final)}\nCosto: ${final.costo:,} · Beneficio: {final.beneficio}\n"
                                       f"Disponible: ${presupuesto - final.costo:,}")
            mejores = " / ".join(nombres(s) for s in exacta.soluciones)
            diferencia = exacta.beneficio - final.beneficio
            comparacion = ("Coincide con el óptimo global." if diferencia == 0
                           else f"Máximo local: faltan {diferencia} unidades de beneficio.")
            self.verificacion.set(f"Comprobación de {exacta.combinaciones} combinaciones\nMejores: {mejores}\n"
                                  f"Beneficio máximo: {exacta.beneficio} unidades.\n{comparacion}")
            self.tabla_productos.delete(*self.tabla_productos.get_children())
            for paso, s in enumerate(resultado.pasos):
                self.tabla_productos.insert("", "end", values=(paso, nombres(s), s.costo, s.beneficio))
            self.listo("productos")
            return True

        def restablecer_lista(self):
            self.texto_lista.set(", ".join(map(numero, LISTA)))
            self.inicio.set("1")
            self.calcular_lista()

        def restablecer_productos(self):
            self.presupuesto.set(str(PRESUPUESTO))
            for variable in self.elegidos.values():
                variable.set(False)
            self.calcular_productos()

        def guardar(self):
            if any(self.pendientes.values()):
                self.estado.set("Calcula primero los cambios pendientes para guardar las gráficas.")
                return
            destino = filedialog.asksaveasfilename(parent=raiz, title="Guardar los dos ejercicios",
                defaultextension=".png", initialfile="Hill_Climbing.png", filetypes=[("Imagen PNG", "*.png")])
            if not destino:
                return
            try:
                ruta = guardar_png(destino, self.lista, self.productos, self.exacta, self.presupuesto_calculado)
            except (OSError, ValueError) as error:
                self.estado.set(f"No se pudo guardar la imagen: {error}")
                return
            self.estado.set(f"Gráficas guardadas: {ruta}")

    return Aplicacion()


def main():
    parser = argparse.ArgumentParser(description="Hill Climbing: lista y productos con presupuesto.")
    parser.add_argument("--lista", default=", ".join(map(numero, LISTA)), help="valores separados por comas; decimales con punto")
    parser.add_argument("--inicio", type=int, default=1, help="posición inicial en la lista, desde 1")
    parser.add_argument("--presupuesto", type=int, default=PRESUPUESTO, help="pesos enteros disponibles")
    parser.add_argument("--seleccion", default="", help="productos iniciales separados por comas; ejemplo A,B")
    parser.add_argument("--terminal", action="store_true", help="mostrar cálculos sin dependencias gráficas")
    parser.add_argument("--sin-ventana", action="store_true", help="mostrar cálculos y exportar PNG sin abrir Tkinter")
    parser.add_argument("--salida", type=Path, help="ruta PNG; activa la exportación sin ventana")
    args = parser.parse_args()
    try:
        valores = leer_lista(args.lista)
        seleccion = tuple(n.strip().upper() for n in args.seleccion.split(",")) if args.seleccion.strip() else ()
        lista = subir_lista(valores, args.inicio - 1)
        resultado = subir_productos(PRODUCTOS, args.presupuesto, seleccion)
        exacta = verificar_optimo(PRODUCTOS, args.presupuesto)
        if args.terminal or args.sin_ventana or args.salida:
            imprimir_resultados(lista, resultado, exacta, args.presupuesto)
            if args.sin_ventana or args.salida:
                from graficas import guardar_png
                print("Imagen guardada:", guardar_png(args.salida or SALIDA, lista, resultado, exacta, args.presupuesto))
            return
        import tkinter as tk
        try:
            raiz = tk.Tk()
        except tk.TclError:
            parser.exit(1, "No se pudo abrir la ventana. Revisa WSLg o usa --terminal o --sin-ventana.\n")
        try:
            crear_interfaz(raiz, valores, args.inicio - 1, args.presupuesto, seleccion)
        except ImportError:
            raiz.destroy()
            raise
        raiz.mainloop()
    except ImportError as error:
        ayuda = ("Instala Tkinter para tu Python (Ubuntu: sudo apt install python3-tk)."
                 if (error.name or "") in ("tkinter", "_tkinter")
                 else "Instala Matplotlib con el requirements.txt de esta práctica.")
        parser.exit(1, ayuda + " Puedes usar --terminal sin dependencias gráficas.\n")
    except (ValueError, OSError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
