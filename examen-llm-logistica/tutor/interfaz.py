"""Chat sencillo, con respuestas en segundo plano y resumen del historial."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from comun.trabajos_tk import TrabajosTk


def iniciar(tutor):
    ventana = tk.Tk()
    ventana.title('Primer ejercicio · Tutor de SQL')
    ventana.geometry('820x680')
    ventana.minsize(680, 560)
    marco = ttk.Frame(ventana, padding=18)
    marco.pack(fill='both', expand=True)
    ttk.Label(marco, text='Tutor de SQL para principiantes', font=('TkDefaultFont', 18, 'bold')).pack(anchor='w')
    ttk.Label(marco, text=f'Modelo local: {tutor.cliente.modelo} · Contexto: las últimas 6 interacciones').pack(anchor='w', pady=6)
    chat = ScrolledText(marco, wrap='word', font=('TkDefaultFont', 11), state='disabled')
    chat.pack(fill='both', expand=True)

    def escribir(nombre, texto):
        chat.configure(state='normal')
        chat.insert('end', f'{nombre}:\n{texto}\n\n')
        chat.configure(state='disabled')
        chat.see('end')

    for mensaje in tutor.historial:
        escribir('Tú' if mensaje['role'] == 'user' else 'Tutor', mensaje['content'])
    pregunta = tk.StringVar()
    entrada = ttk.Entry(marco, textvariable=pregunta)
    entrada.pack(fill='x', pady=(12, 8))
    fila = ttk.Frame(marco)
    fila.pack(fill='x')
    estado = tk.StringVar(value='Escribe una pregunta sobre SQL.')
    ttk.Label(marco, textvariable=estado).pack(anchor='w', pady=8)
    progreso = ttk.Progressbar(marco, mode='indeterminate')
    progreso.pack(fill='x')
    trabajos = TrabajosTk(ventana, estado, progreso)

    def enviar(evento=None):
        texto = pregunta.get().strip()
        if not texto:
            messagebox.showinfo('Pregunta vacía', 'Escribe qué quieres aprender.', parent=ventana)
            return

        def mostrar(resultado):
            respuesta, ms = resultado
            escribir('Tú', texto)
            escribir('Tutor', respuesta)
            if pregunta.get().strip() == texto:
                pregunta.set('')
            estado.set(f'Respuesta guardada · {ms / 1000:.1f} s')

        trabajos.ejecutar('Consultando el modelo local…', lambda: tutor.preguntar(texto), mostrar)

    def resumen():
        trabajos.ejecutar('Preparando resumen…', tutor.resumir, lambda texto: escribir('Resumen del historial', texto))

    def reiniciar():
        if trabajos.ocupado:
            return
        if messagebox.askyesno('Nueva conversación', '¿Borrar el historial local de esta conversación?', default='no', parent=ventana):
            try:
                tutor.reiniciar()
            except OSError:
                messagebox.showerror('Historial', 'No se pudo guardar el historial vacío.', parent=ventana)
                return
            chat.configure(state='normal')
            chat.delete('1.0', 'end')
            chat.configure(state='disabled')

    def exportar():
        import json
        from pathlib import Path
        ruta = filedialog.asksaveasfilename(parent=ventana, defaultextension='.json', filetypes=[('Historial JSON', '*.json')])
        if ruta:
            try:
                Path(ruta).write_text(json.dumps(tutor.historial, ensure_ascii=False, indent=2), encoding='utf-8')
            except OSError:
                messagebox.showerror('Exportación', 'No se pudo guardar el archivo.', parent=ventana)

    for etiqueta, accion in [('Enviar', enviar), ('Resumen de mi historial', resumen), ('Exportar', exportar), ('Nueva conversación', reiniciar)]:
        ttk.Button(fila, text=etiqueta, command=accion).pack(side='left', padx=(0, 8))
    entrada.bind('<Return>', enviar)
    entrada.focus_set()
    ventana.protocol('WM_DELETE_WINDOW', lambda: ventana.destroy() if trabajos.puede_cerrar() else None)
    ventana.mainloop()
