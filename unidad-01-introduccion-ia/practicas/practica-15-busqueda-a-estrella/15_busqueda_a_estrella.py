"""Práctica 15: heurísticas y A* de A a J, con Tkinter o terminal."""
import argparse
import math

from busqueda_a_estrella import (
    GRAFO_ORIGINAL, HEURISTICA_ORIGINAL, a_estrella,
    analizar_heuristica, validar_problema,
)


POSICIONES = {
    "A": (.46, .09), "B": (.24, .28), "C": (.70, .28),
    "D": (.10, .48), "E": (.37, .48), "F": (.61, .48), "G": (.89, .48),
    "H": (.08, .68), "I": (.64, .68), "J": (.72, .89),
}


def texto_numero(valor):
    return "—" if valor is None else f"{valor:g}"


def texto_ruta(nodos):
    return " → ".join(nodos) if nodos else "—"


def texto_diagnostico(diagnostico):
    if diagnostico.admisible:
        return "Las estimaciones no superan el costo real restante: h es admisible para este grafo."
    estados = ", ".join(diagnostico.sobreestimados)
    return (f"h sobreestima el costo restante en {estados}. Se conservan estos valores; "
            "con rutas alternativas, una sobreestimación puede impedir obtener el costo mínimo.")


def imprimir_resultado(resultado, diagnostico):
    print("\nPRÁCTICA 15 · A* · Inicio A · Meta J · f(n) = g(n) + h(n)")
    print("Costos iniciales: 1 por arista (la imagen no incluye pesos).")
    print("Heurísticas:", ", ".join(f"{n}={h}" for n, h in HEURISTICA_ORIGINAL.items()))
    for numero, paso in enumerate(resultado.pasos, 1):
        print(f"\n{numero}. {paso.mensaje}")
        print("   Camino actual:", texto_ruta(paso.camino))
        pendientes = "; ".join(f"{a.estado}: g={a.g:g}, h={a.h:g}, f={a.f:g}" for a in paso.frontera)
        print("   Frontera por menor f(n):", pendientes or "vacía")
    print("\nOrden de extracción:", texto_ruta(resultado.orden))
    if resultado.ruta is None:
        print("No existe una ruta de A a J.")
    else:
        print("Ruta encontrada:", texto_ruta(resultado.ruta))
        print(f"Costo recorrido: {resultado.costo:g} | Profundidad: {len(resultado.ruta) - 1}")
    print(texto_diagnostico(diagnostico))


def crear_interfaz(raiz):
    """Se importa Tkinter aquí para permitir la ejecución sin ventana."""
    import tkinter as tk
    from tkinter import ttk

    class Aplicacion:
        def __init__(self):
            self.grafo, self.heuristica = validar_problema(GRAFO_ORIGINAL, HEURISTICA_ORIGINAL)
            self.resultado = None
            self.indice = 0
            self.temporizador = None
            self.editor = None
            self.datos = {clave: tk.StringVar(value="—") for clave in ("actual", "g", "h", "f", "profundidad")}
            self.orden, self.camino = tk.StringVar(), tk.StringVar()
            self.estado, self.resumen = tk.StringVar(), tk.StringVar()
            self.nota_heuristica = tk.StringVar()
            raiz.title("Práctica 15 · Heurísticas y búsqueda A*")
            raiz.geometry("1240x880")
            raiz.minsize(1100, 790)
            raiz.configure(bg="#f4f7fc")
            estilo = ttk.Style(raiz)
            estilo.theme_use("clam")
            estilo.configure("TFrame", background="#f4f7fc")
            estilo.configure("TLabel", background="#f4f7fc", foreground="#20304e", font=("DejaVu Sans", 10))
            estilo.configure("Titulo.TLabel", font=("DejaVu Sans", 24, "bold"))
            estilo.configure("Dato.TLabel", font=("DejaVu Sans", 12, "bold"))
            estilo.configure("TButton", padding=(10, 8), font=("DejaVu Sans", 10))
            estilo.configure("Treeview", rowheight=27, font=("DejaVu Sans", 9))
            principal = ttk.Frame(raiz, padding=22)
            principal.pack(fill="both", expand=True)
            ttk.Label(principal, text="LABORATORIO DE BÚSQUEDA · UTVT · PRÁCTICA 15").pack(anchor="w")
            ttk.Label(principal, text="A*: costo + estimación", style="Titulo.TLabel").pack(anchor="w", pady=(4, 6))
            ttk.Label(principal, text="Objetivo: A → J   |   g(n): recorrido   ·   h(n): falta estimada   ·   f(n) = g(n) + h(n)").pack(anchor="w")
            ttk.Label(principal, text="La imagen no indica pesos: se inicia con costo 1 por arista. Los costos y las estimaciones son editables.").pack(anchor="w", pady=(4, 0))
            controles = ttk.Frame(principal)
            controles.pack(fill="x", pady=16)
            self.boton_calcular = ttk.Button(controles, text="Calcular A → J", command=self.calcular)
            self.boton_paso = ttk.Button(controles, text="Paso siguiente", command=self.siguiente)
            self.boton_animar = ttk.Button(controles, text="Animar", command=self.animar)
            self.boton_resultado = ttk.Button(controles, text="Ver resultado", command=self.ver_resultado)
            for boton in (self.boton_calcular, self.boton_paso, self.boton_animar, self.boton_resultado):
                boton.pack(side="left", padx=(0, 8))
            ttk.Button(controles, text="Editar costos y h(n)", command=self.editar_valores).pack(side="left", padx=(0, 8))
            ttk.Button(controles, text="Reiniciar", command=self.reiniciar).pack(side="left")

            indicadores = ttk.Frame(principal)
            indicadores.pack(fill="x", pady=(0, 16))
            for titulo, clave in (("ESTADO ACTUAL", "actual"), ("RECORRIDO g(n)", "g"),
                                  ("ESTIMACIÓN h(n)", "h"), ("TOTAL ESTIMADO f(n)", "f"),
                                  ("PROFUNDIDAD", "profundidad")):
                bloque = ttk.Frame(indicadores)
                bloque.pack(side="left", padx=(0, 27))
                ttk.Label(bloque, text=titulo).pack(anchor="w")
                ttk.Label(bloque, textvariable=self.datos[clave], style="Dato.TLabel").pack(anchor="w", pady=(3, 0))

            cuerpo = ttk.Frame(principal)
            cuerpo.columnconfigure(0, weight=1)
            cuerpo.columnconfigure(1, weight=0, minsize=430)
            cuerpo.rowconfigure(0, weight=1)
            dibujo = ttk.Frame(cuerpo)
            dibujo.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
            self.canvas = tk.Canvas(dibujo, background="white", highlightthickness=1,
                                    highlightbackground="#d9e2ef", width=690, height=450)
            self.canvas.bind("<Configure>", lambda evento: self.dibujar())
            self.leyenda = ttk.Label(dibujo, text="Verde: camino actual · Ámbar: nodo extraído\nDentro del nodo: h(n). Junto a la arista: costo del movimiento.")
            self.leyenda.pack(side="bottom", anchor="w", pady=(8, 0))
            self.canvas.pack(fill="both", expand=True)
            lateral = ttk.Frame(cuerpo)
            lateral.grid(row=0, column=1, sticky="nsew")
            for titulo, variable in (("ORDEN DE EXTRACCIÓN", self.orden), ("CAMINO ACTUAL", self.camino)):
                ttk.Label(lateral, text=titulo).pack(anchor="w", pady=(0, 4))
                ttk.Label(lateral, textvariable=variable, style="Dato.TLabel", wraplength=430).pack(anchor="w", pady=(0, 10))
            ttk.Label(lateral, text="La frontera prioriza el menor f(n).\nLos empates respetan el orden de llegada.").pack(anchor="w", pady=(0, 10))
            pestanas = ttk.Notebook(lateral)
            pestanas.pack(fill="both", expand=True)
            self.tabla_frontera = self.crear_tabla(pestanas, "Frontera", (
                ("estado", "Nodo", 50), ("g", "g(n)", 55), ("h", "h(n)", 55),
                ("f", "f(n)", 55), ("camino", "Camino pendiente", 200)))
            self.tabla_pasos = self.crear_tabla(pestanas, "Pasos", (
                ("paso", "Paso", 45), ("estado", "Nodo", 50), ("g", "g(n)", 55),
                ("h", "h(n)", 55), ("f", "f(n)", 55), ("prof", "Prof.", 50), ("evento", "Evento", 90)))
            self.tabla_heuristicas = self.crear_tabla(pestanas, "Heurísticas", (
                ("estado", "Nodo", 50), ("h", "h(n)", 55),
                ("real", "Costo real a J", 115), ("revision", "Revisión", 175)))
            # Reservar el pie antes del área expandible evita recortar el resultado
            # al reducir la ventana. El lienzo absorbe el cambio de tamaño.
            self.pie = ttk.Frame(principal)
            self.pie.pack(side="bottom", fill="x")
            ttk.Separator(self.pie).pack(fill="x", pady=(12, 8))
            ttk.Label(self.pie, textvariable=self.estado, wraplength=1035).pack(anchor="w")
            ttk.Label(self.pie, textvariable=self.resumen, style="Dato.TLabel", wraplength=1035).pack(anchor="w", pady=(6, 0))
            ttk.Label(self.pie, textvariable=self.nota_heuristica, wraplength=1035, foreground="#825025").pack(anchor="w", pady=(6, 0))
            cuerpo.pack(fill="both", expand=True)
            raiz.protocol("WM_DELETE_WINDOW", self.cerrar)
            self.reiniciar()

        def crear_tabla(self, pestanas, titulo, columnas):
            marco = ttk.Frame(pestanas)
            pestanas.add(marco, text=titulo)
            marco.columnconfigure(0, weight=1)
            marco.rowconfigure(0, weight=1)
            tabla = ttk.Treeview(marco, columns=tuple(c[0] for c in columnas), show="headings", height=7)
            for nombre, etiqueta, ancho in columnas:
                tabla.heading(nombre, text=etiqueta)
                tabla.column(nombre, width=ancho, minwidth=ancho, stretch=nombre in ("camino", "revision"), anchor="w")
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

        def reiniciar(self):
            self.pausar()
            self.resultado = None
            self.indice = 0
            for variable in self.datos.values():
                variable.set("—")
            self.orden.set("—")
            self.camino.set("—")
            self.estado.set("Pulsa Calcular: cada paso extraerá el estado pendiente con menor f(n).")
            self.resumen.set("Al inicio: g(A)=0, h(A)=" + texto_numero(self.heuristica['A']) + ", f(A)=" + texto_numero(self.heuristica['A']))
            for tabla in (self.tabla_frontera, self.tabla_pasos, self.tabla_heuristicas):
                tabla.delete(*tabla.get_children())
            diagnostico = analizar_heuristica(self.grafo, self.heuristica)
            self.nota_heuristica.set(texto_diagnostico(diagnostico))
            for nodo, h in self.heuristica.items():
                real = diagnostico.distancias[nodo]
                revision = "Sin ruta dirigida a J" if math.isinf(real) else ("Sobreestima" if nodo in diagnostico.sobreestimados else "No sobreestima")
                self.tabla_heuristicas.insert("", "end", values=(nodo, texto_numero(h),
                                              "Sin ruta" if math.isinf(real) else texto_numero(real), revision))
            self.actualizar_botones()
            self.dibujar()

        def calcular(self):
            self.reiniciar()
            try:
                self.resultado = a_estrella(self.grafo, self.heuristica)
            except ValueError as error:
                self.estado.set(str(error))
                return
            self.mostrar_paso()

        def actualizar_botones(self):
            disponible = self.resultado is not None and self.indice < len(self.resultado.pasos) - 1
            for boton in (self.boton_paso, self.boton_animar, self.boton_resultado):
                boton.configure(state="normal" if disponible else "disabled")

        def mostrar_paso(self):
            paso = self.resultado.pasos[self.indice]
            self.datos["actual"].set(paso.actual or "—")
            for clave, valor in (("g", paso.g), ("h", paso.h), ("f", paso.f), ("profundidad", paso.profundidad)):
                self.datos[clave].set(texto_numero(valor))
            self.orden.set(texto_ruta(paso.visitados))
            self.camino.set(texto_ruta(paso.camino))
            self.estado.set(f"Paso {self.indice + 1}/{len(self.resultado.pasos)} · {paso.mensaje}")
            if self.indice == len(self.resultado.pasos) - 1:
                self.pausar()
                self.resumen.set("Sin ruta de A a J." if self.resultado.ruta is None else
                                 f"Ruta: {texto_ruta(self.resultado.ruta)}   |   Costo recorrido: {self.resultado.costo:g}   |   h(J)=0")
            else:
                self.resumen.set(f"Siguiente en la frontera: {paso.frontera[0].estado}, f(n)={paso.frontera[0].f:g}." if paso.frontera else "La frontera quedó vacía.")
            self.tabla_frontera.delete(*self.tabla_frontera.get_children())
            for a in paso.frontera:
                self.tabla_frontera.insert("", "end", values=(a.estado, texto_numero(a.g), texto_numero(a.h), texto_numero(a.f), texto_ruta(a.camino)))
            self.tabla_pasos.delete(*self.tabla_pasos.get_children())
            for numero, p in enumerate(self.resultado.pasos[:self.indice + 1], 1):
                ultimo = self.tabla_pasos.insert("", "end", values=(numero, p.actual or "—", texto_numero(p.g),
                    texto_numero(p.h), texto_numero(p.f), texto_numero(p.profundidad), p.evento))
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
                self.temporizador = raiz.after(950, self.avanzar_animacion)

        def avanzar_animacion(self):
            self.temporizador = None
            if self.resultado and self.indice < len(self.resultado.pasos) - 1:
                self.indice += 1
                self.mostrar_paso()
                if self.indice < len(self.resultado.pasos) - 1:
                    self.temporizador = raiz.after(950, self.avanzar_animacion)

        def ver_resultado(self):
            self.pausar()
            if self.resultado:
                self.indice = len(self.resultado.pasos) - 1
                self.mostrar_paso()

        def editar_valores(self):
            self.pausar()
            if self.editor is not None:
                self.editor.lift()
                return
            self.editor = tk.Toplevel(raiz)
            self.editor.title("Costos del recorrido y estimaciones a J")
            self.editor.transient(raiz)
            self.editor.resizable(False, False)
            panel = ttk.Frame(self.editor, padding=20)
            panel.pack(fill="both", expand=True)
            ttk.Label(panel, text="Costos y heurísticas son valores distintos", style="Dato.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
            ttk.Label(panel, text="Usa números finitos no negativos. h(J) se conserva en 0.\nLos cambios solo duran durante esta sesión.").grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 14))
            self.campos_costos, self.campos_h = {}, {}
            for columna, titulo in enumerate(("Costo de cada arista", "h(n): estimación hasta J")):
                bloque = ttk.Frame(panel, padding=(0, 0, 25, 0))
                bloque.grid(row=2, column=columna, sticky="nw")
                ttk.Label(bloque, text=titulo, style="Dato.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
                datos = [((o, d), f"{o} → {d}", c) for o, vecinos in self.grafo.items() for d, c in vecinos.items()] if columna == 0 else [(n, n, h) for n, h in self.heuristica.items()]
                campos = self.campos_costos if columna == 0 else self.campos_h
                for fila, (clave, etiqueta, valor) in enumerate(datos, 1):
                    ttk.Label(bloque, text=etiqueta).grid(row=fila, column=0, sticky="w", pady=4)
                    variable = tk.StringVar(value=texto_numero(valor))
                    campos[clave] = variable
                    ttk.Entry(bloque, textvariable=variable, width=12,
                              state="readonly" if columna == 1 and clave == "J" else "normal").grid(row=fila, column=1, padx=(12, 0))
            self.estado_editor = tk.StringVar(value="Aplicar reinicia el recorrido con los nuevos valores.")
            ttk.Label(panel, textvariable=self.estado_editor, wraplength=570, foreground="#825025").grid(row=3, column=0, columnspan=2, sticky="w", pady=12)
            botones = ttk.Frame(panel)
            botones.grid(row=4, column=0, columnspan=2, sticky="w")
            ttk.Button(botones, text="Aplicar", command=self.aplicar_valores).pack(side="left", padx=(0, 8))
            ttk.Button(botones, text="Cargar originales", command=self.cargar_originales).pack(side="left", padx=(0, 8))
            ttk.Button(botones, text="Cancelar", command=self.cerrar_editor).pack(side="left")
            self.editor.protocol("WM_DELETE_WINDOW", self.cerrar_editor)
            self.editor.grab_set()

        def cargar_originales(self):
            for (o, d), variable in self.campos_costos.items():
                variable.set(texto_numero(GRAFO_ORIGINAL[o][d]))
            for nodo, variable in self.campos_h.items():
                variable.set(texto_numero(HEURISTICA_ORIGINAL[nodo]))
            self.estado_editor.set("Costos unitarios y heurísticas del ejercicio cargados. Pulsa Aplicar.")

        def aplicar_valores(self):
            grafo = {nodo: dict(vecinos) for nodo, vecinos in self.grafo.items()}
            h = {}
            try:
                for (o, d), variable in self.campos_costos.items():
                    etiqueta = f"costo {o} → {d}"
                    grafo[o][d] = float(variable.get().strip().replace(",", "."))
                for nodo, variable in self.campos_h.items():
                    etiqueta = f"h({nodo})"
                    h[nodo] = float(variable.get().strip().replace(",", "."))
            except ValueError:
                self.estado_editor.set(f"Escribe un número válido en {etiqueta}.")
                return False
            try:
                grafo, h = validar_problema(grafo, h)
                # Validación atómica: ninguna edición se aplica si las sumas desbordan.
                a_estrella(grafo, h)
                analizar_heuristica(grafo, h)
            except ValueError as error:
                self.estado_editor.set(str(error))
                return False
            self.grafo, self.heuristica = grafo, h
            self.cerrar_editor()
            self.reiniciar()
            self.estado.set("Valores actualizados. Pulsa Calcular para iniciar otra búsqueda.")
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
            aristas = set(zip(camino, camino[1:]))
            for origen, vecinos in self.grafo.items():
                for destino, costo in vecinos.items():
                    x1, y1 = posiciones[origen]
                    x2, y2 = posiciones[destino]
                    distancia = math.hypot(x2 - x1, y2 - y1) or 1
                    ux, uy = (x2 - x1) / distancia, (y2 - y1) / distancia
                    activo = (origen, destino) in aristas
                    self.canvas.create_line(x1 + ux * 27, y1 + uy * 27, x2 - ux * 27, y2 - uy * 27,
                                            fill="#228466" if activo else "#bbc9dc", width=4 if activo else 2,
                                            arrow="last", arrowshape=(10, 12, 5))
                    etiqueta = self.canvas.create_text((x1 + x2) / 2 - uy * 17, (y1 + y2) / 2 + ux * 17,
                                                       text=texto_numero(costo), font=("DejaVu Sans", 10, "bold"), fill="#4b627e")
                    caja = self.canvas.bbox(etiqueta)
                    fondo = self.canvas.create_rectangle(caja[0] - 3, caja[1] - 2, caja[2] + 3, caja[3] + 2, fill="white", outline="white")
                    self.canvas.tag_lower(fondo, etiqueta)
            for nodo, (x, y) in posiciones.items():
                color = "#e4eaf3" if paso and nodo in paso.visitados else "white"
                color = "#c3e8d8" if nodo in camino else color
                color = "#ffd58f" if paso and nodo == paso.actual else color
                self.canvas.create_oval(x - 27, y - 27, x + 27, y + 27, fill=color, outline="#6a82a4", width=2)
                self.canvas.create_text(x, y - 9, text=nodo, font=("DejaVu Sans", 14, "bold"), fill="#20304e")
                self.canvas.create_text(x, y + 11, text=f"h={self.heuristica[nodo]:g}", font=("DejaVu Sans", 9), fill="#42577a")
                if nodo in ("A", "J"):
                    self.canvas.create_text(x + 42, y, text="Inicio" if nodo == "A" else "Meta", anchor="w", fill="#42577a", font=("DejaVu Sans", 9))

        def cerrar(self):
            self.pausar()
            self.cerrar_editor()
            raiz.destroy()

    return Aplicacion()


def main():
    parser = argparse.ArgumentParser(description="Búsqueda A* de A a J: f(n) = g(n) + h(n).")
    parser.add_argument("--terminal", action="store_true", help="mostrar el recorrido sin abrir una ventana")
    args = parser.parse_args()
    if args.terminal:
        imprimir_resultado(a_estrella(GRAFO_ORIGINAL, HEURISTICA_ORIGINAL),
                           analizar_heuristica(GRAFO_ORIGINAL, HEURISTICA_ORIGINAL))
        return
    try:
        import tkinter as tk
    except ImportError:
        parser.exit(1, "Falta Tkinter. En Ubuntu/WSL instala python3-tk, o utiliza --terminal.\n")
    try:
        raiz = tk.Tk()
    except tk.TclError:
        parser.exit(1, "No se pudo abrir la ventana. Revisa WSLg o utiliza --terminal.\n")
    crear_interfaz(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
