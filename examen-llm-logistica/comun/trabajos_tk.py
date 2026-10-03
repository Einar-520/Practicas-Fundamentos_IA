"""Ejecutar tareas lentas sin modificar widgets desde un hilo secundario."""
import queue
import threading
from tkinter import messagebox


class TrabajosTk:
    def __init__(self, ventana, estado, progreso):
        self.ventana, self.estado, self.progreso = ventana, estado, progreso
        self.cola = queue.Queue()
        self.ocupado = False
        self.cerrado = False
        ventana.after(80, self._recibir)

    def ejecutar(self, mensaje, tarea, al_terminar):
        if self.ocupado:
            messagebox.showinfo('Proceso en curso', 'Espera a que termine la operación actual.', parent=self.ventana)
            return False
        self.ocupado = True
        self.estado.set(mensaje)
        self.progreso.start(12)

        def trabajar():
            try:
                self.cola.put((True, tarea(), al_terminar))
            except Exception as error:
                self.cola.put((False, error, al_terminar))

        threading.Thread(target=trabajar, daemon=True).start()
        return True

    def _recibir(self):
        if self.cerrado:
            return
        try:
            correcto, resultado, callback = self.cola.get_nowait()
        except queue.Empty:
            pass
        else:
            self.ocupado = False
            self.progreso.stop()
            self.estado.set('Listo' if correcto else 'La operación no se completó')
            if correcto:
                callback(resultado)
            else:
                messagebox.showerror('No se pudo completar', str(resultado), parent=self.ventana)
        self.ventana.after(80, self._recibir)

    def puede_cerrar(self):
        if self.ocupado:
            messagebox.showinfo('Espera un momento', 'Hay una operación en curso. Espera antes de cerrar.', parent=self.ventana)
            return False
        self.cerrado = True
        return True
