"""Revisión humana individual del conjunto de evaluación, sin editar código."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from logismart.dominio.modelos import CATEGORIAS, PRIORIDADES


def abrir_revision(app, registros, ruta_var):
    ventana = tk.Toplevel(app.root)
    ventana.title('Etiquetado manual del corpus')
    ventana.geometry('850x630')
    ventana.transient(app.root)
    ventana.grab_set()
    marco = ttk.Frame(ventana, padding=16); marco.pack(fill='both', expand=True)
    contador, categoria, prioridad, confirmado = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.BooleanVar()
    indice = [0]
    ttk.Label(marco, textvariable=contador, font=('TkDefaultFont', 14, 'bold')).pack(anchor='w')
    texto = ScrolledText(marco, wrap='word', height=15, state='disabled'); texto.pack(fill='both', expand=True, pady=10)
    for etiqueta, var, opciones in [('Categoría esperada', categoria, CATEGORIAS), ('Prioridad esperada', prioridad, PRIORIDADES)]:
        ttk.Label(marco, text=etiqueta).pack(anchor='w')
        ttk.Combobox(marco, textvariable=var, values=opciones, state='readonly').pack(fill='x', pady=(2, 8))
    ttk.Checkbutton(marco, text='He leído este correo y confirmé manualmente ambas etiquetas', variable=confirmado).pack(anchor='w')
    def cargar():
        d = registros[indice[0]]
        contador.set(f"Correo {indice[0] + 1}/{len(registros)} · {d['id']} · {d['registro']}")
        texto.configure(state='normal'); texto.delete('1.0', 'end')
        texto.insert('1.0', f"Remitente: {d['remitente']}\nAsunto: {d['asunto']}\n\n{d['cuerpo']}")
        texto.configure(state='disabled')
        categoria.set(d['categoria_esperada']); prioridad.set(d['prioridad_esperada'])
        confirmado.set(d.get('revisado_humano') is True)
    def conservar():
        d = registros[indice[0]]
        d.update(categoria_esperada=categoria.get(), prioridad_esperada=prioridad.get(), revisado_humano=confirmado.get(),
                 revisor=app.config.operador if confirmado.get() else '')
    def mover(paso):
        conservar(); indice[0] = max(0, min(len(registros) - 1, indice[0] + paso)); cargar()
    def guardar():
        conservar()
        ruta = filedialog.asksaveasfilename(parent=ventana, initialfile='correos_revisados.json', defaultextension='.json', filetypes=[('JSON', '*.json')])
        if ruta:
            try:
                Path(ruta).write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding='utf-8')
            except OSError:
                messagebox.showerror('No se pudo guardar', 'Revisa la carpeta de destino.', parent=ventana); return
            ruta_var.set(ruta)
            messagebox.showinfo('Etiquetas guardadas', f"Confirmadas: {sum(d.get('revisado_humano') is True for d in registros)}/{len(registros)}", parent=ventana)
            ventana.destroy()
    barra = ttk.Frame(marco); barra.pack(fill='x', pady=12)
    for etiqueta, accion in [('Anterior', lambda: mover(-1)), ('Siguiente', lambda: mover(1)), ('Guardar conjunto revisado', guardar)]:
        ttk.Button(barra, text=etiqueta, command=accion).pack(side='left', padx=(0, 8))
    cargar()
