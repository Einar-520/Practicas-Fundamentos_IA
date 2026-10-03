"""Práctica 11: rutas de un árbol binario, con Tkinter y salida en terminal."""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class Nodo:
    valor: str
    izquierdo: Nodo | None = None
    derecho: Nodo | None = None


def construir_arbol() -> Nodo:
    """A tiene a B y C; B tiene a D; C tiene a E y F."""
    return Nodo(
        'A',
        izquierdo=Nodo('B', izquierdo=Nodo('D')),
        derecho=Nodo('C', izquierdo=Nodo('E'), derecho=Nodo('F')),
    )


def buscar_rutas(raiz: Nodo | None, destino: str | None = None) -> list[list[str]]:
    """Buscar todas las rutas al destino, o hasta las hojas si se omite el destino."""
    if destino is not None:
        if not isinstance(destino, str) or not destino.strip():
            raise ValueError('El destino debe ser el nombre de un nodo.')
        destino = destino.strip().upper()
    rutas = []

    def explorar(nodo: Nodo | None, camino: list[str]) -> None:
        if nodo is None:
            return
        ruta = camino + [nodo.valor]
        es_hoja = nodo.izquierdo is None and nodo.derecho is None
        if (destino is None and es_hoja) or nodo.valor == destino:
            rutas.append(ruta)
        # Se recorre primero la rama izquierda y después la derecha.
        explorar(nodo.izquierdo, ruta)
        explorar(nodo.derecho, ruta)

    explorar(raiz, [])
    return rutas


def mostrar_rutas(titulo: str, rutas: list[list[str]]) -> None:
    print(f'\n{titulo}')
    if not rutas:
        print('No se encontró ninguna ruta.')
        return
    for numero, ruta in enumerate(rutas, start=1):
        print(f'{numero}. {" -> ".join(ruta)}')
    print(f'Total de rutas: {len(rutas)}')


def abrir_interfaz(arbol: Nodo) -> None:
    """Dibujar el árbol y consultar sus rutas en una ventana sencilla."""
    # La terminal funciona incluso cuando Tkinter no está instalado.
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError as error:
        raise SystemExit(
            'Falta Tkinter. En Ubuntu/WSL ejecuta: sudo apt install python3-tk\n'
            'También puedes ejecutar esta práctica con --terminal.'
        ) from error

    try:
        ventana = tk.Tk()
    except tk.TclError as error:
        raise SystemExit(
            'No se pudo abrir la ventana de Tkinter. Comprueba que tu sesión '
            'tenga soporte gráfico; en WSL se necesita WSLg o un servidor gráfico.\n'
            'Puedes ver las rutas sin ventana añadiendo --terminal.'
        ) from error

    ventana.title('Práctica 11 · Árbol binario')
    ventana.geometry('660x620')
    ventana.minsize(600, 580)
    contenido = ttk.Frame(ventana, padding=20)
    contenido.pack(fill='both', expand=True)
    ttk.Label(contenido, text='Árbol binario',
              font=('TkDefaultFont', 19, 'bold')).pack(anchor='w')
    ttk.Label(contenido, text='Explora las rutas desde A y encuentra el camino hasta F.'
              ).pack(anchor='w', pady=(4, 14))

    lienzo = tk.Canvas(contenido, height=270, background='white',
                       highlightthickness=1, highlightbackground='#cbd5e1')
    lienzo.pack(fill='both', expand=True)
    botones = ttk.Frame(contenido)
    botones.pack(fill='x', pady=14)
    panel = ttk.LabelFrame(contenido, text='Resultado', padding=12)
    panel.pack(fill='x')
    resultado = tk.StringVar(master=ventana)
    detalle = tk.StringVar(master=ventana)
    ttk.Label(panel, textvariable=resultado, justify='left',
              font=('TkDefaultFont', 12)).pack(anchor='w')
    ttk.Label(contenido, textvariable=detalle, wraplength=550,
              justify='left').pack(anchor='w', pady=(10, 0))

    ruta_resaltada: list[str] = []

    def dibujar_arbol(evento=None) -> None:
        """Las conexiones dibujadas proceden del mismo árbol que se consulta."""
        ancho = evento.width if evento is not None else lienzo.winfo_width()
        alto = evento.height if evento is not None else lienzo.winfo_height()
        ancho, alto = max(ancho, 540), max(alto, 230)
        lienzo.delete('all')
        conexiones = set(zip(ruta_resaltada, ruta_resaltada[1:]))
        paso = (alto - 80) / 2

        def dibujar(nodo: Nodo, x: float, y: float, espacio: float) -> None:
            for hijo, sentido in ((nodo.izquierdo, -1), (nodo.derecho, 1)):
                if hijo is None:
                    continue
                siguiente_x, siguiente_y = x + sentido * espacio, y + paso
                seleccionada = (nodo.valor, hijo.valor) in conexiones
                lienzo.create_line(x, y, siguiente_x, siguiente_y,
                                   fill='#15803d' if seleccionada else '#94a3b8',
                                   width=4 if seleccionada else 2)
                dibujar(hijo, siguiente_x, siguiente_y, espacio / 2)
            seleccionado = nodo.valor in ruta_resaltada
            lienzo.create_oval(x - 23, y - 23, x + 23, y + 23,
                               fill='#15803d' if seleccionado else '#eff6ff',
                               outline='#15803d' if seleccionado else '#2563eb',
                               width=2)
            lienzo.create_text(x, y, text=nodo.valor,
                               fill='white' if seleccionado else '#1e3a8a',
                               font=('TkDefaultFont', 14, 'bold'))

        dibujar(arbol, ancho / 2, 40, ancho / 4)

    def mostrar(destino: str | None = None) -> None:
        rutas = buscar_rutas(arbol, destino)
        ruta_resaltada[:] = rutas[0] if destino and rutas else []
        titulo = 'Rutas desde A hasta F:' if destino else 'Rutas desde A hasta las hojas:'
        lineas = [titulo]
        lineas.extend(f'{numero}. {" → ".join(ruta)}'
                      for numero, ruta in enumerate(rutas, start=1))
        lineas.append(f'Total de rutas: {len(rutas)}')
        resultado.set('\n'.join(lineas))
        detalle.set(
            'El camino A → C → F está marcado en verde. Es la única ruta hasta F.'
            if destino else
            'Cada ruta termina en una hoja: D, E o F. Pulsa «Buscar A → F» para resaltarla.'
        )
        dibujar_arbol()

    ttk.Button(botones, text='Buscar A → F', command=lambda: mostrar('F')
               ).pack(side='left', padx=(0, 10))
    ttk.Button(botones, text='Ver todas las rutas', command=mostrar).pack(side='left')
    lienzo.bind('<Configure>', dibujar_arbol)
    mostrar()
    ventana.mainloop()


def main() -> None:
    argumentos = argparse.ArgumentParser(
        description='Explora las rutas del árbol binario con Tkinter o en terminal.'
    )
    argumentos.add_argument('--terminal', action='store_true',
                            help='mostrar las rutas sin abrir la ventana gráfica')
    opciones = argumentos.parse_args()
    arbol = construir_arbol()
    print('PRÁCTICA 11: RUTAS EN UN ÁRBOL BINARIO')
    print('Raíz: A')
    print('Rama izquierda: B, con hijo izquierdo D.')
    print('Rama derecha: C, con hijo izquierdo E e hijo derecho F.')
    mostrar_rutas('Todas las rutas desde A hasta una hoja:', buscar_rutas(arbol))
    mostrar_rutas('Rutas desde A hasta F:', buscar_rutas(arbol, 'F'))
    print('\nEn este árbol existe una sola ruta de A a F: A -> C -> F.')
    if not opciones.terminal:
        abrir_interfaz(arbol)


if __name__ == '__main__':
    main()
