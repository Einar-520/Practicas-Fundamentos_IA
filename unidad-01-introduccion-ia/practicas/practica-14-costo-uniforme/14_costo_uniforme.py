"""Práctica 14: UCS con heapq, interfaz Tkinter y salida en terminal."""
import argparse
import math

from busqueda_ucs import GRAFO_ORIGINAL, ucs, validar_grafo


POSICIONES = {
    "A": (.45, .11), "B": (.24, .34), "C": (.67, .34),
    "D": (.10, .59), "E": (.35, .59), "F": (.61, .59), "G": (.89, .59),
    "H": (.18, .83), "I": (.43, .83), "J": (.73, .83),
}


def texto_ruta(nodos):
    return " → ".join(nodos) if nodos else "—"


def texto_costo(valor):
    return "—" if valor is None else f"{valor:g}"


def imprimir_resultado(inicio, objetivo, resultado):
    print(f"\nUCS · Inicio: {inicio} · Objetivo: {objetivo}")
    for numero, paso in enumerate(resultado.pasos, 1):
        print(f"{numero}. {paso.mensaje}")
        pendientes = "; ".join(f"{texto_ruta(a.camino)} [{a.costo:g}]" for a in paso.frontera)
        print("   Frontera de menor a mayor costo:", pendientes or "vacía")
    print("Orden de visita:", texto_ruta(resultado.orden))
    if resultado.ruta is None:
        print("No existe una ruta entre los estados seleccionados.")
    else:
        print("Ruta de costo mínimo:", texto_ruta(resultado.ruta))
        print(f"Costo total: {resultado.costo:g}")
        print(f"Profundidad de la solución: {len(resultado.ruta) - 1}")


def crear_interfaz(raiz, inicio="A", objetivo="J"):
    """Tkinter solo se importa al elegir el modo gráfico."""
    import tkinter as tk
    from tkinter import ttk

    class Aplicacion:
        def __init__(self):
            self.grafo = validar_grafo(GRAFO_ORIGINAL)
            self.resultado = None
            self.indice = 0
            self.temporizador = None
            self.editor = None
            self.inicio = tk.StringVar(value=inicio)
            self.objetivo = tk.StringVar(value=objetivo)
            self.costo_actual = tk.StringVar(value="—")
            self.menor_pendiente = tk.StringVar(value="—")
            self.profundidad = tk.StringVar(value="—")
            self.cantidad_visitados = tk.StringVar(value="0")
            self.orden = tk.StringVar(value="—")
            self.camino = tk.StringVar(value="—")
            self.estado = tk.StringVar()
            self.resumen = tk.StringVar()
            raiz.title("Práctica 14 · Búsqueda de costo uniforme (UCS)")
            raiz.geometry("1200x820")
            raiz.minsize(1050, 760)
            raiz.configure(bg="#f5f8f7")
            estilo = ttk.Style(raiz)
            estilo.theme_use("clam")
            estilo.configure("TFrame", background="#f5f8f7")
            estilo.configure("TLabel", background="#f5f8f7", foreground="#173d34", font=("DejaVu Sans", 10))
            estilo.configure("Titulo.TLabel", font=("DejaVu Sans", 24, "bold"))
            estilo.configure("Dato.TLabel", font=("DejaVu Sans", 12, "bold"))
            estilo.configure("TButton", padding=(10, 8), font=("DejaVu Sans", 10))
            estilo.configure("Treeview", rowheight=26, font=("DejaVu Sans", 9))
            principal = ttk.Frame(raiz, padding=24)
            principal.pack(fill="both", expand=True)
            ttk.Label(principal, text="LABORATORIO DE BÚSQUEDA · UTVT").pack(anchor="w")
            ttk.Label(principal, text="El camino de menor costo", style="Titulo.TLabel").pack(anchor="w", pady=(4, 8))
            ttk.Label(principal, text="UCS con heapq · Prioridad = costo acumulado g(n) · Sin heurística").pack(anchor="w")
            controles = ttk.Frame(principal)
            controles.pack(fill="x", pady=18)
            for etiqueta, variable in (("Inicio", self.inicio), ("Objetivo", self.objetivo)):
                bloque = ttk.Frame(controles)
                bloque.pack(side="left", padx=(0, 16))
                ttk.Label(bloque, text=etiqueta).pack(anchor="w", pady=(0, 5))
                selector = ttk.Combobox(bloque, textvariable=variable, values=list(self.grafo), state="readonly", width=5)
                selector.pack()
                selector.bind("<<ComboboxSelected>>", self.reiniciar)
            self.boton_calcular = ttk.Button(controles, text="Calcular", command=self.calcular)
            self.boton_paso = ttk.Button(controles, text="Paso siguiente", command=self.siguiente)
            self.boton_animar = ttk.Button(controles, text="Animar", command=self.animar)
            self.boton_resultado = ttk.Button(controles, text="Ver resultado", command=self.ver_resultado)
            for boton in (self.boton_calcular, self.boton_paso, self.boton_animar, self.boton_resultado):
                boton.pack(side="left", anchor="s", padx=(0, 8))
            ttk.Button(controles, text="Editar costos", command=self.editar_costos).pack(side="left", anchor="s")

            indicadores = ttk.Frame(principal)
            indicadores.pack(fill="x", pady=(0, 16))
            for titulo, variable in (("COSTO ACTUAL g(n)", self.costo_actual),
                                     ("MENOR COSTO PENDIENTE", self.menor_pendiente),
                                     ("PROFUNDIDAD", self.profundidad),
                                     ("ESTADOS VISITADOS", self.cantidad_visitados)):
                bloque = ttk.Frame(indicadores)
                bloque.pack(side="left", padx=(0, 30))
                ttk.Label(bloque, text=titulo).pack(anchor="w")
                ttk.Label(bloque, textvariable=variable, style="Dato.TLabel").pack(anchor="w", pady=(3, 0))

            cuerpo = ttk.Frame(principal)
            cuerpo.pack(fill="both", expand=True)
            cuerpo.columnconfigure(0, weight=1)
            cuerpo.columnconfigure(1, weight=0, minsize=395)
            cuerpo.rowconfigure(0, weight=1)
            dibujo = ttk.Frame(cuerpo)
            dibujo.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
            self.canvas = tk.Canvas(dibujo, background="white", highlightthickness=1,
                                    highlightbackground="#dce6e1", width=630, height=380)
            self.canvas.pack(fill="both", expand=True)
            self.canvas.bind("<Configure>", lambda evento: self.dibujar())
            ttk.Label(dibujo, text="Verde: camino actual · Ámbar: nodo extraído\nNúmero junto a cada arista: costo del movimiento", wraplength=600).pack(anchor="w", pady=(10, 0))
            lateral = ttk.Frame(cuerpo)
            lateral.grid(row=0, column=1, sticky="nsew")
            for titulo, variable in (("ORDEN DE VISITA", self.orden), ("CAMINO ACTUAL", self.camino)):
                ttk.Label(lateral, text=titulo).pack(anchor="w", pady=(0, 5))
                ttk.Label(lateral, textvariable=variable, style="Dato.TLabel", wraplength=395).pack(anchor="w", pady=(0, 12))
            ttk.Label(lateral, text="La frontera muestra primero el menor g(n).\nEn empates se respeta el orden de llegada.", wraplength=395).pack(anchor="w", pady=(0, 12))
            pestanas = ttk.Notebook(lateral)
            pestanas.pack(fill="both", expand=True)
            self.tabla_frontera = self.crear_tabla(pestanas, "Frontera", (
                ("turno", "N.º", 40), ("estado", "Nodo", 50),
                ("costo", "g(n)", 65), ("camino", "Camino pendiente", 220)))
            self.tabla_pasos = self.crear_tabla(pestanas, "Pasos", (
                ("paso", "Paso", 50), ("evento", "Evento", 110),
                ("estado", "Nodo", 60), ("costo", "g(n)", 80), ("prof", "Prof.", 65)))
            ttk.Separator(principal).pack(fill="x", pady=(16, 10))
            ttk.Label(principal, textvariable=self.estado, wraplength=980).pack(anchor="w")
            ttk.Label(principal, textvariable=self.resumen, style="Dato.TLabel", wraplength=980).pack(anchor="w", pady=(7, 0))
            raiz.protocol("WM_DELETE_WINDOW", self.cerrar)
            self.reiniciar()

        def crear_tabla(self, pestanas, titulo, columnas):
            marco = ttk.Frame(pestanas)
            pestanas.add(marco, text=titulo)
            marco.columnconfigure(0, weight=1)
            marco.rowconfigure(0, weight=1)
            tabla = ttk.Treeview(marco, columns=tuple(c[0] for c in columnas), show="headings", height=6)
            for nombre, etiqueta, ancho in columnas:
                tabla.heading(nombre, text=etiqueta)
                tabla.column(nombre, width=ancho, minwidth=ancho, stretch=nombre in ("camino", "evento"), anchor="w")
            vertical = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
            horizontal = ttk.Scrollbar(marco, orient="horizontal", command=tabla.xview)
            tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
            tabla.grid(row=0, column=0, sticky="nsew")
            vertical.grid(row=0, column=1, sticky="ns")
            horizontal.grid(row=1, column=0, sticky="ew")
            return tabla

        def pausar(self):
            if self.temporizador is not None:
                raiz.after_cancel(self.temporizador)
                self.temporizador = None
            self.boton_animar.configure(text="Animar")

        def reiniciar(self, evento=None):
            self.pausar()
            self.resultado = None
            self.indice = 0
            for variable in (self.costo_actual, self.menor_pendiente, self.profundidad, self.orden, self.camino):
                variable.set("—")
            self.cantidad_visitados.set("0")
            self.estado.set("Selecciona inicio y objetivo. Cada extracción elige el menor costo acumulado pendiente.")
            self.resumen.set("Pulsa Calcular para comenzar. El costo del inicio es 0.")
            for tabla in (self.tabla_frontera, self.tabla_pasos):
                tabla.delete(*tabla.get_children())
            self.actualizar_botones()
            self.dibujar()

        def calcular(self):
            self.reiniciar()
            try:
                self.resultado = ucs(self.grafo, self.inicio.get(), self.objetivo.get())
            except ValueError as error:
                self.estado.set(str(error))
                return
            imprimir_resultado(self.inicio.get(), self.objetivo.get(), self.resultado)
            self.mostrar_paso()

        def actualizar_botones(self):
            disponible = self.resultado is not None and self.indice < len(self.resultado.pasos) - 1
            for boton in (self.boton_paso, self.boton_animar, self.boton_resultado):
                boton.configure(state="normal" if disponible else "disabled")

        def mostrar_paso(self):
            paso = self.resultado.pasos[self.indice]
            self.costo_actual.set(texto_costo(paso.costo))
            self.menor_pendiente.set(texto_costo(paso.frontera[0].costo) if paso.frontera else "Vacía")
            self.profundidad.set(str(paso.profundidad) if paso.profundidad is not None else "—")
            self.cantidad_visitados.set(str(len(paso.visitados)))
            self.orden.set(texto_ruta(paso.visitados))
            self.camino.set(texto_ruta(paso.camino))
            self.estado.set(f"Paso {self.indice + 1}/{len(self.resultado.pasos)} · {paso.mensaje}")
            if self.indice == len(self.resultado.pasos) - 1:
                self.pausar()
                self.resumen.set("Sin ruta: el objetivo no es alcanzable desde el inicio." if self.resultado.ruta is None else
                                 f"Ruta óptima: {texto_ruta(self.resultado.ruta)}   |   Costo mínimo: {self.resultado.costo:g}")
            else:
                self.resumen.set("Búsqueda en curso. La meta se confirma cuando sale de la cola con el costo mínimo.")
            self.tabla_frontera.delete(*self.tabla_frontera.get_children())
            for numero, alternativa in enumerate(paso.frontera, 1):
                self.tabla_frontera.insert("", "end", values=(numero, alternativa.estado,
                                          texto_costo(alternativa.costo), texto_ruta(alternativa.camino)))
            self.tabla_pasos.delete(*self.tabla_pasos.get_children())
            for numero, registro in enumerate(self.resultado.pasos[:self.indice + 1], 1):
                ultimo = self.tabla_pasos.insert("", "end", values=(numero, registro.evento, registro.actual or "—",
                                                texto_costo(registro.costo), registro.profundidad if registro.profundidad is not None else "—"))
            self.tabla_pasos.see(ultimo)
            self.actualizar_botones()
            self.dibujar()

        def siguiente(self):
            self.pausar()
            if self.resultado and self.indice < len(self.resultado.pasos) - 1:
                self.indice += 1
                self.mostrar_paso()

        def animar(self):
            if self.temporizador is not None:
                self.pausar()
            elif self.resultado and self.indice < len(self.resultado.pasos) - 1:
                self.boton_animar.configure(text="Pausar")
                self.temporizador = raiz.after(850, self.avanzar_animacion)

        def avanzar_animacion(self):
            self.temporizador = None
            if self.resultado and self.indice < len(self.resultado.pasos) - 1:
                self.indice += 1
                self.mostrar_paso()
                if self.indice < len(self.resultado.pasos) - 1:
                    self.temporizador = raiz.after(850, self.avanzar_animacion)

        def ver_resultado(self):
            self.pausar()
            if self.resultado:
                self.indice = len(self.resultado.pasos) - 1
                self.mostrar_paso()

        def editar_costos(self):
            self.pausar()
            if self.editor is not None:
                self.editor.lift()
                return
            self.editor = tk.Toplevel(raiz)
            self.editor.title("Costos de las aristas")
            self.editor.transient(raiz)
            self.editor.resizable(False, False)
            panel = ttk.Frame(self.editor, padding=20)
            panel.pack(fill="both", expand=True)
            ttk.Label(panel, text="Modifica los costos", style="Dato.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
            ttk.Label(panel, text="Acepta cero y decimales; no acepta negativos.\nLos cambios duran hasta cerrar el programa.").grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 12))
            self.campos_costos = {}
            for fila, (origen, destino) in enumerate(((o, d) for o, vecinos in self.grafo.items() for d in vecinos), 2):
                ttk.Label(panel, text=f"{origen} → {destino}").grid(row=fila, column=0, sticky="w", pady=4)
                variable = tk.StringVar(value=texto_costo(self.grafo[origen][destino]))
                self.campos_costos[origen, destino] = variable
                ttk.Entry(panel, textvariable=variable, width=18).grid(row=fila, column=1, sticky="ew", padx=(24, 0))
            self.estado_editor = tk.StringVar(value="Pulsa Aplicar para reiniciar el recorrido con estos valores.")
            ttk.Label(panel, textvariable=self.estado_editor, wraplength=410, foreground="#944717").grid(row=12, column=0, columnspan=2, sticky="w", pady=12)
            botones = ttk.Frame(panel)
            botones.grid(row=13, column=0, columnspan=2, sticky="ew")
            ttk.Button(botones, text="Aplicar", command=self.aplicar_costos).pack(side="left", padx=(0, 8))
            ttk.Button(botones, text="Cargar originales", command=self.cargar_originales).pack(side="left", padx=(0, 8))
            ttk.Button(botones, text="Cancelar", command=self.cerrar_editor).pack(side="left")
            self.editor.protocol("WM_DELETE_WINDOW", self.cerrar_editor)
            self.editor.grab_set()

        def cargar_originales(self):
            for (origen, destino), variable in self.campos_costos.items():
                variable.set(texto_costo(GRAFO_ORIGINAL[origen][destino]))
            self.estado_editor.set("Valores del pizarrón cargados. Pulsa Aplicar para utilizarlos.")

        def aplicar_costos(self):
            nuevos = {nodo: dict(vecinos) for nodo, vecinos in self.grafo.items()}
            for (origen, destino), variable in self.campos_costos.items():
                try:
                    nuevos[origen][destino] = float(variable.get().strip().replace(",", "."))
                except ValueError:
                    self.estado_editor.set(f"Escribe un número válido en {origen} → {destino}.")
                    return False
            try:
                nuevos = validar_grafo(nuevos)
            except ValueError as error:
                self.estado_editor.set(str(error))
                return False
            self.grafo = nuevos
            self.cerrar_editor()
            self.reiniciar()
            self.estado.set("Costos actualizados. Pulsa Calcular para iniciar una nueva búsqueda.")
            return True

        def cerrar_editor(self):
            if self.editor is not None:
                self.editor.grab_release()
                self.editor.destroy()
                self.editor = None

        def dibujar(self):
            self.canvas.delete("all")
            ancho, alto = self.canvas.winfo_width(), self.canvas.winfo_height()
            posiciones = {nodo: (x * ancho, y * alto) for nodo, (x, y) in POSICIONES.items()}
            paso = self.resultado.pasos[self.indice] if self.resultado else None
            camino = paso.camino if paso else ()
            aristas_camino = set(zip(camino, camino[1:]))
            for origen, vecinos in self.grafo.items():
                for destino, costo in vecinos.items():
                    x1, y1 = posiciones[origen]
                    x2, y2 = posiciones[destino]
                    distancia = math.hypot(x2 - x1, y2 - y1) or 1
                    ux, uy = (x2 - x1) / distancia, (y2 - y1) / distancia
                    activo = (origen, destino) in aristas_camino
                    self.canvas.create_line(x1 + ux * 24, y1 + uy * 24, x2 - ux * 24, y2 - uy * 24,
                                            fill="#207f6a" if activo else "#b8ccc3", width=4 if activo else 2,
                                            arrow="last", arrowshape=(12, 14, 5))
                    etiqueta = self.canvas.create_text((x1 + x2) / 2 - uy * 17, (y1 + y2) / 2 + ux * 17,
                                                       text=texto_costo(costo), font=("DejaVu Sans", 11, "bold"), fill="#315d4d")
                    caja = self.canvas.bbox(etiqueta)
                    fondo = self.canvas.create_rectangle(caja[0] - 3, caja[1] - 2, caja[2] + 3, caja[3] + 2,
                                                         fill="white", outline="white")
                    self.canvas.tag_lower(fondo, etiqueta)
            for nodo, (x, y) in posiciones.items():
                color = "#e7edea" if paso and nodo in paso.visitados else "white"
                color = "#b9e1d3" if nodo in camino else color
                color = "#ffd38a" if paso and nodo == paso.actual else color
                self.canvas.create_oval(x - 24, y - 24, x + 24, y + 24, fill=color, outline="#557c6c", width=2)
                self.canvas.create_text(x, y, text=nodo, font=("DejaVu Sans", 17, "bold"), fill="#173d34")
                etiquetas = []
                if nodo == self.inicio.get():
                    etiquetas.append("Inicio")
                if nodo == self.objetivo.get():
                    etiquetas.append("Meta")
                if etiquetas:
                    self.canvas.create_text(x, y + 39, text=" / ".join(etiquetas), fill="#416554", font=("DejaVu Sans", 10))

        def cerrar(self):
            self.pausar()
            self.cerrar_editor()
            raiz.destroy()

    return Aplicacion()


def main():
    parser = argparse.ArgumentParser(description="Búsqueda de costo uniforme (UCS) con heapq.")
    parser.add_argument("--terminal", action="store_true", help="mostrar la búsqueda sin abrir una ventana")
    parser.add_argument("--inicio", type=str.upper, choices=GRAFO_ORIGINAL, default="A")
    parser.add_argument("--objetivo", type=str.upper, choices=GRAFO_ORIGINAL, default="J")
    args = parser.parse_args()
    if args.terminal:
        imprimir_resultado(args.inicio, args.objetivo, ucs(GRAFO_ORIGINAL, args.inicio, args.objetivo))
        return
    try:
        import tkinter as tk
    except ImportError:
        parser.exit(1, "Falta Tkinter. En Ubuntu/WSL instala python3-tk, o utiliza --terminal.\n")
    try:
        raiz = tk.Tk()
    except tk.TclError:
        parser.exit(1, "No se pudo abrir la ventana. Revisa WSLg o utiliza --terminal.\n")
    crear_interfaz(raiz, args.inicio, args.objetivo)
    raiz.mainloop()


if __name__ == "__main__":
    main()
