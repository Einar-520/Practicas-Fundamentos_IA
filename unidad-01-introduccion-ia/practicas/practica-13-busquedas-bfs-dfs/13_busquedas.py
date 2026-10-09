"""Práctica 13: interfaz Tkinter y terminal para BFS y DFS."""
import argparse
import math

from busquedas import GRAFO_BFS, GRAFO_DFS, bfs, dfs


EJERCICIOS = {"BFS": (GRAFO_BFS, bfs), "DFS": (GRAFO_DFS, dfs)}
POSICIONES = {
    "BFS": {"A": (.18, .24), "B": (.50, .24), "C": (.82, .24),
            "D": (.18, .70), "E": (.50, .70), "F": (.82, .70)},
    "DFS": {"A": (.50, .15), "B": (.27, .43), "C": (.77, .43),
            "D": (.13, .78), "E": (.42, .78), "F": (.77, .78)},
}


def texto_ruta(nodos):
    return " → ".join(nodos) if nodos else "—"


def imprimir_resultado(algoritmo, inicio, objetivo, resultado):
    print(f"\n{algoritmo} | Inicio: {inicio} | Objetivo: {objetivo}")
    for paso in resultado.pasos:
        print(f"{paso.evento}: {paso.mensaje}")
    print("Orden de visita:", texto_ruta(resultado.orden))
    if resultado.ruta is None:
        print("No existe una ruta entre los estados seleccionados.")
    else:
        print("Ruta encontrada:", texto_ruta(resultado.ruta))
        print(f"Costo: {resultado.costo} movimiento(s).")


def crear_interfaz(raiz, algoritmo="BFS", inicio="A", objetivo="F"):
    """Importar o ejecutar --terminal no requiere una instalación de Tkinter."""
    import tkinter as tk
    from tkinter import ttk

    class Aplicacion:
        def __init__(self):
            self.resultado = None
            self.indice = 0
            self.temporizador = None
            self.algoritmo = tk.StringVar(value=algoritmo)
            self.inicio = tk.StringVar(value=inicio)
            self.objetivo = tk.StringVar(value=objetivo)
            self.estado = tk.StringVar(value="Selecciona un ejercicio y pulsa Calcular.")
            self.orden = tk.StringVar(value="—")
            self.camino = tk.StringVar(value="—")
            self.pendientes = tk.StringVar(value="—")
            self.resumen = tk.StringVar(value="La ruta aparecerá al terminar el recorrido.")
            self.tipo_pendientes = tk.StringVar()
            self.descripcion = tk.StringVar()
            raiz.title("Práctica 13 · Búsquedas BFS y DFS")
            raiz.geometry("1100x730")
            raiz.minsize(980, 680)
            raiz.configure(bg="#f5f8f7")
            estilo = ttk.Style(raiz)
            estilo.theme_use("clam")
            estilo.configure("TFrame", background="#f5f8f7")
            estilo.configure("TLabel", background="#f5f8f7", foreground="#173d34", font=("DejaVu Sans", 10))
            estilo.configure("Titulo.TLabel", font=("DejaVu Sans", 24, "bold"))
            estilo.configure("Dato.TLabel", font=("DejaVu Sans", 12, "bold"))
            estilo.configure("TButton", padding=(12, 8), font=("DejaVu Sans", 10))
            estilo.configure("Treeview", rowheight=26, font=("DejaVu Sans", 9))

            principal = ttk.Frame(raiz, padding=24)
            principal.pack(fill="both", expand=True)
            ttk.Label(principal, text="LABORATORIO DE BÚSQUEDA · UTVT").pack(anchor="w")
            ttk.Label(principal, text="Del inicio a la meta", style="Titulo.TLabel").pack(anchor="w", pady=(4, 8))
            ttk.Label(principal, textvariable=self.descripcion).pack(anchor="w")

            controles = ttk.Frame(principal)
            controles.pack(fill="x", pady=20)
            for etiqueta, variable, opciones, ancho in (
                ("Ejercicio", self.algoritmo, ["BFS", "DFS"], 9),
                ("Inicio", self.inicio, list(GRAFO_BFS), 5),
                ("Objetivo", self.objetivo, list(GRAFO_BFS), 5),
            ):
                bloque = ttk.Frame(controles)
                bloque.pack(side="left", padx=(0, 16))
                ttk.Label(bloque, text=etiqueta).pack(anchor="w", pady=(0, 5))
                selector = ttk.Combobox(bloque, textvariable=variable, values=opciones,
                                        state="readonly", width=ancho)
                selector.pack()
                selector.bind("<<ComboboxSelected>>", self.reiniciar)
            ttk.Button(controles, text="Calcular", command=self.calcular).pack(side="left", anchor="s", padx=(0, 8))
            self.boton_paso = ttk.Button(controles, text="Paso siguiente", command=self.siguiente)
            self.boton_paso.pack(side="left", anchor="s", padx=(0, 8))
            self.boton_animar = ttk.Button(controles, text="Animar", command=self.animar)
            self.boton_animar.pack(side="left", anchor="s", padx=(0, 8))
            self.boton_resultado = ttk.Button(controles, text="Ver resultado", command=self.ver_resultado)
            self.boton_resultado.pack(side="left", anchor="s")

            cuerpo = ttk.Frame(principal)
            cuerpo.pack(fill="both", expand=True)
            cuerpo.columnconfigure(0, weight=1)
            cuerpo.columnconfigure(1, weight=0, minsize=350)
            cuerpo.rowconfigure(0, weight=1)
            dibujo = ttk.Frame(cuerpo)
            dibujo.grid(row=0, column=0, sticky="nsew", padx=(0, 24))
            self.canvas = tk.Canvas(dibujo, background="white", highlightthickness=1,
                                    highlightbackground="#dce6e1", width=530, height=340)
            self.canvas.pack(fill="both", expand=True)
            self.canvas.bind("<Configure>", lambda evento: self.dibujar())
            ttk.Label(dibujo, text="Verde: camino actual · Ámbar: nodo actual\nGris: visitado fuera del camino",
                      wraplength=510).pack(anchor="w", pady=(12, 0))

            lateral = ttk.Frame(cuerpo, width=350)
            lateral.grid(row=0, column=1, sticky="nsew")
            for etiqueta, variable in (("ORDEN DE VISITA", self.orden),
                                       ("CAMINO ACTUAL", self.camino),
                                       (self.tipo_pendientes, self.pendientes)):
                kwargs = {"text": etiqueta} if isinstance(etiqueta, str) else {"textvariable": etiqueta}
                ttk.Label(lateral, **kwargs).pack(anchor="w", pady=(0, 5))
                ttk.Label(lateral, textvariable=variable, style="Dato.TLabel", wraplength=350).pack(anchor="w", pady=(0, 16))
            ttk.Label(lateral, text="El orden de visita no es la ruta solución.", wraplength=350).pack(anchor="w", pady=(0, 10))
            tabla = ttk.Frame(lateral)
            tabla.pack(fill="both", expand=True)
            self.traza = ttk.Treeview(tabla, columns=("paso", "evento", "nodo"), show="headings", height=5)
            for nombre, ancho in (("paso", 50), ("evento", 160), ("nodo", 70)):
                self.traza.heading(nombre, text=nombre.capitalize())
                self.traza.column(nombre, width=ancho, stretch=nombre == "evento", anchor="w")
            barra = ttk.Scrollbar(tabla, orient="vertical", command=self.traza.yview)
            self.traza.configure(yscrollcommand=barra.set)
            barra.pack(side="right", fill="y")
            self.traza.pack(side="left", fill="both", expand=True)
            ttk.Separator(principal).pack(fill="x", pady=(18, 12))
            ttk.Label(principal, textvariable=self.estado, wraplength=1000).pack(anchor="w")
            ttk.Label(principal, textvariable=self.resumen, style="Dato.TLabel", wraplength=1000).pack(anchor="w", pady=(7, 0))
            raiz.protocol("WM_DELETE_WINDOW", self.cerrar)
            self.reiniciar()

        def pausar(self):
            if self.temporizador is not None:
                raiz.after_cancel(self.temporizador)
                self.temporizador = None
            self.boton_animar.configure(text="Animar")

        def reiniciar(self, evento=None):
            self.pausar()
            self.resultado = None
            self.indice = 0
            es_bfs = self.algoritmo.get() == "BFS"
            self.descripcion.set("BFS · Grafo no dirigido · Explora por niveles con una cola." if es_bfs else
                                 "DFS · Árbol dirigido · Profundiza y retrocede con llamadas recursivas.")
            self.tipo_pendientes.set("COLA · PRIMERO A LA IZQUIERDA" if es_bfs else "PILA DE LLAMADAS · CIMA A LA DERECHA")
            for variable in (self.orden, self.camino, self.pendientes):
                variable.set("—")
            self.estado.set("Cada ejercicio conserva su grafo original. Pulsa Calcular para comenzar.")
            self.resumen.set("La ruta aparecerá al terminar el recorrido.")
            self.traza.delete(*self.traza.get_children())
            self.actualizar_botones()
            self.dibujar()

        def calcular(self):
            self.pausar()
            grafo, buscar = EJERCICIOS[self.algoritmo.get()]
            self.resultado = buscar(grafo, self.inicio.get(), self.objetivo.get())
            self.indice = 0
            imprimir_resultado(self.algoritmo.get(), self.inicio.get(), self.objetivo.get(), self.resultado)
            self.mostrar_paso()

        def actualizar_botones(self):
            disponible = self.resultado is not None and self.indice < len(self.resultado.pasos) - 1
            for boton in (self.boton_paso, self.boton_animar, self.boton_resultado):
                boton.configure(state="normal" if disponible else "disabled")

        def mostrar_paso(self):
            paso = self.resultado.pasos[self.indice]
            self.orden.set(texto_ruta(paso.visitados))
            self.camino.set(texto_ruta(paso.camino))
            self.pendientes.set(" · ".join(paso.pendientes) or "Vacía")
            self.estado.set(f"Paso {self.indice + 1}/{len(self.resultado.pasos)} · {paso.mensaje}")
            final = self.indice == len(self.resultado.pasos) - 1
            if final:
                self.pausar()
                if self.resultado.ruta is None:
                    self.resumen.set("Sin ruta: el objetivo no es alcanzable desde el inicio.")
                else:
                    self.resumen.set(f"Ruta: {texto_ruta(self.resultado.ruta)}   |   Costo: {self.resultado.costo} movimiento(s)")
            else:
                self.resumen.set("Recorrido en curso; la ruta solución se mostrará al llegar a la meta.")
            self.traza.delete(*self.traza.get_children())
            for numero, registro in enumerate(self.resultado.pasos[:self.indice + 1], 1):
                ultimo = self.traza.insert("", "end", values=(numero, registro.evento, registro.actual or "—"))
            self.traza.see(ultimo)
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
                self.temporizador = raiz.after(750, self.avanzar_animacion)

        def avanzar_animacion(self):
            self.temporizador = None
            if self.resultado and self.indice < len(self.resultado.pasos) - 1:
                self.indice += 1
                self.mostrar_paso()
                if self.indice < len(self.resultado.pasos) - 1:
                    self.temporizador = raiz.after(750, self.avanzar_animacion)

        def ver_resultado(self):
            self.pausar()
            if self.resultado:
                self.indice = len(self.resultado.pasos) - 1
                self.mostrar_paso()

        def dibujar(self):
            self.canvas.delete("all")
            algoritmo = self.algoritmo.get()
            grafo, _ = EJERCICIOS[algoritmo]
            ancho, alto = self.canvas.winfo_width(), self.canvas.winfo_height()
            posiciones = {nodo: (x * ancho, y * alto) for nodo, (x, y) in POSICIONES[algoritmo].items()}
            paso = self.resultado.pasos[self.indice] if self.resultado else None
            camino = paso.camino if paso else ()
            aristas_camino = set(zip(camino, camino[1:]))
            trazadas = set()
            for origen, vecinos in grafo.items():
                for destino in vecinos:
                    if algoritmo == "BFS" and (destino, origen) in trazadas:
                        continue
                    trazadas.add((origen, destino))
                    x1, y1 = posiciones[origen]
                    x2, y2 = posiciones[destino]
                    distancia = math.hypot(x2 - x1, y2 - y1) or 1
                    dx, dy = (x2 - x1) / distancia * 25, (y2 - y1) / distancia * 25
                    activo = (origen, destino) in aristas_camino or (algoritmo == "BFS" and (destino, origen) in aristas_camino)
                    self.canvas.create_line(x1 + dx, y1 + dy, x2 - dx, y2 - dy,
                                            fill="#207f6a" if activo else "#c5d5cf",
                                            width=4 if activo else 2,
                                            arrow="last" if algoritmo == "DFS" else "none", arrowshape=(12, 14, 5))
            for nodo, (x, y) in posiciones.items():
                color = "#e7edea" if paso and nodo in paso.visitados else "white"
                color = "#b9e1d3" if nodo in camino else color
                color = "#ffd38a" if paso and nodo == paso.actual else color
                self.canvas.create_oval(x - 24, y - 24, x + 24, y + 24,
                                        fill=color, outline="#557c6c", width=2)
                self.canvas.create_text(x, y, text=nodo, font=("DejaVu Sans", 17, "bold"), fill="#173d34")
                etiquetas = []
                if nodo == self.inicio.get():
                    etiquetas.append("Inicio")
                if nodo == self.objetivo.get():
                    etiquetas.append("Meta")
                if etiquetas:
                    self.canvas.create_text(x, y + 40, text=" / ".join(etiquetas), fill="#416554", font=("DejaVu Sans", 10))

        def cerrar(self):
            self.pausar()
            raiz.destroy()

    return Aplicacion()


def main():
    parser = argparse.ArgumentParser(description="Búsquedas BFS y DFS del profesor, con interfaz o terminal.")
    parser.add_argument("--terminal", action="store_true", help="mostrar los pasos sin abrir una ventana")
    parser.add_argument("--algoritmo", type=str.upper, choices=EJERCICIOS, default="BFS")
    parser.add_argument("--inicio", type=str.upper, choices=GRAFO_BFS, default="A")
    parser.add_argument("--objetivo", type=str.upper, choices=GRAFO_BFS, default="F")
    args = parser.parse_args()
    if args.terminal:
        grafo, buscar = EJERCICIOS[args.algoritmo]
        imprimir_resultado(args.algoritmo, args.inicio, args.objetivo,
                           buscar(grafo, args.inicio, args.objetivo))
        return
    try:
        import tkinter as tk
    except ImportError:
        parser.exit(1, "Falta Tkinter. En Ubuntu/WSL instala python3-tk, o utiliza --terminal.\n")
    try:
        raiz = tk.Tk()
    except tk.TclError:
        parser.exit(1, "No se pudo abrir la ventana. Revisa el soporte gráfico WSLg o utiliza --terminal.\n")
    crear_interfaz(raiz, args.algoritmo, args.inicio, args.objetivo)
    raiz.mainloop()


if __name__ == "__main__":
    main()
