"""Flujos reales de Tkinter. Se omiten únicamente si no existe una pantalla."""
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from comun.ollama_local import OllamaLocal
from logismart.dominio.modelos import Configuracion
from logismart.infraestructura.repositorio import DemoRepositorio
from logismart.servicios.aplicacion import Aplicacion
from logismart.servicios.clasificador import ClasificadorHibrido
from logismart.servicios.demostracion import cargar_demo


@unittest.skipUnless(os.environ.get('DISPLAY') or os.name == 'nt', 'Requiere pantalla gráfica o Xvfb.')
class TestFlujosGUI(unittest.TestCase):
    def setUp(self):
        from logismart.presentacion.app import VentanaLogiSmart
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = DemoRepositorio(Path(self.tmp.name)/'demo.json')
        config = Configuracion(usar_llm=False)
        servicio = Aplicacion(self.repo, ClasificadorHibrido(OllamaLocal(),False), config)
        cargar_demo(servicio)
        self.errores = []
        self.parche = patch('tkinter.messagebox.showerror', side_effect=lambda titulo, mensaje, **_: self.errores.append(mensaje))
        self.parche.start()
        self.app = VentanaLogiSmart(servicio)
        self.app.root.report_callback_exception = lambda t, e, tb: self.errores.append(str(e))
        self.bombear(.3)

    def tearDown(self):
        self.bombear(.1)
        self.app.trabajos.cerrado = True
        # Cancela los after pendientes antes de crear otra instancia de Tk en la prueba siguiente.
        for tarea in self.app.root.tk.call('after', 'info'):
            self.app.root.after_cancel(tarea)
        self.app.root.destroy()
        self.parche.stop()
        self.tmp.cleanup()
        self.assertEqual(self.errores, [])

    def bombear(self, segundos=.2):
        limite = time.monotonic() + segundos
        while time.monotonic() < limite or self.app.trabajos.ocupado:
            self.app.root.update()
            time.sleep(.01)
            if time.monotonic() > limite + 5:
                self.fail('La interfaz no terminó la operación en cinco segundos.')

    def formulario(self):
        from logismart.presentacion.componentes import Formulario
        return next(w for w in self.app.root.winfo_children() if isinstance(w, Formulario))

    def test_camion_alta_edicion_baja(self):
        pagina = self.app.camiones
        pagina.editar(False); self.bombear()
        f = self.formulario()
        for k, v in {'placa':'XYZ-222-D','camion_id':'CAM-222','empresa':'Empresa prueba',
                     'autorizacion':True,'certificacion_conductor':True,'certificado_id':'CERT-222','certificacion_hasta':'2030-01-01'}.items():
            f.variables[k].set(v)
        f.boton_guardar.invoke(); self.bombear()
        d = self.repo.listar('camiones',{'camion_id':'CAM-222'})[0]
        pagina.tabla.tree.selection_set(d['_id']); pagina.editar(True); self.bombear()
        f = self.formulario(); f.variables['empresa'].set('Empresa corregida')
        f.boton_guardar.invoke(); self.bombear()
        self.assertEqual(self.repo.obtener('camiones',d['_id'])['empresa'],'Empresa corregida')
        pagina.tabla.tree.selection_set(d['_id'])
        with patch('tkinter.messagebox.askyesno',return_value=True): pagina.eliminar()
        self.bombear()
        self.assertEqual(self.repo.listar('camiones',{'camion_id':'CAM-222'}),[])

    def test_acceso_y_previsualizacion(self):
        self.app.accesos.editar(False); self.bombear()
        f = self.formulario()
        for k, v in {'camion_id':'CAM-101','placa':'ABC-101-D','P':True,'Q':False,'R':True,'S':True,'H':True,'T':False}.items():
            f.variables[k].set(v)
        textos = [w.cget('text') for w in f.extra.winfo_children() if w.winfo_class()=='TLabel']
        self.assertTrue(any('INSPECCION' in t and 'A=True' in t for t in textos))
        f.boton_guardar.invoke(); self.bombear()
        self.assertEqual(self.repo.listar('accesos',{'camion_id':'CAM-101'})[0]['resultado'],'inspeccion')

    def test_correo_clasificado_desde_formulario(self):
        self.app.incidentes.editar(False); self.bombear()
        f = self.formulario()
        f.variables['asunto'].set('Urgente: fuga')
        f.textos['cuerpo'].insert('1.0','El CAM-102 presenta un derrame de químico inflamable.')
        f.boton_guardar.invoke(); self.bombear()
        d = self.repo.listar('incidentes')[0]
        self.assertEqual(d['clasificacion']['prioridad'],'critica')
        self.assertTrue(d['requiere_revision_humana'])

    def test_navegacion_y_grafica(self):
        for i, pagina in enumerate(self.app.paginas):
            self.app.menu.selection_clear(0,'end'); self.app.menu.selection_set(i)
            self.app._cambiar_pagina(); self.app.root.update()
            self.assertGreater(pagina.winfo_width(),600)
        self.app.riesgos.actualizar(); self.bombear()
        self.assertEqual(len(self.app.figura_riesgos.axes[0].patches),12)


@unittest.skipUnless(os.environ.get('DISPLAY') or os.name == 'nt', 'Requiere pantalla gráfica o Xvfb.')
class TestTutorGUI(unittest.TestCase):
    def test_chat_y_resumen_con_controles_reales(self):
        import tkinter as tk
        from tkinter import ttk
        from tkinter.scrolledtext import ScrolledText
        from tutor.interfaz import iniciar
        from tutor.servicio import TutorSQL
        cliente = Mock()
        cliente.modelo = 'doble_de_prueba'
        cliente.chat.side_effect = [('SELECT titulo FROM libros;', 1.0), ('Se consultaron títulos de libros con SELECT.', 1.0)]
        errores = []
        root = tk.Tk()
        root.report_callback_exception = lambda t, e, tb: errores.append(str(e))
        def descendientes(widget):
            for hijo in widget.winfo_children():
                yield hijo
                yield from descendientes(hijo)
        def enviar():
            entrada = next(w for w in descendientes(root) if isinstance(w, ttk.Entry))
            entrada.insert(0, '¿Cómo consulto los títulos?')
            next(w for w in descendientes(root) if isinstance(w, ttk.Button) and w.cget('text') == 'Enviar').invoke()
        def resumir():
            next(w for w in descendientes(root) if isinstance(w, ttk.Button) and w.cget('text') == 'Resumen de mi historial').invoke()
        capturado = []
        def finalizar():
            texto = next(w for w in descendientes(root) if isinstance(w, ScrolledText))
            capturado.append(texto.get('1.0', 'end'))
            for tarea in root.tk.call('after', 'info'): root.after_cancel(tarea)
            root.destroy()
        with tempfile.TemporaryDirectory() as tmp:
            tutor = TutorSQL(cliente, Path(tmp)/'historial.json')
            root.after(150, enviar); root.after(450, resumir); root.after(850, finalizar)
            with patch('tkinter.Tk', return_value=root): iniciar(tutor)
            self.assertEqual(len(tutor.historial), 2)
        self.assertEqual(errores, [])
        self.assertIn('SELECT titulo FROM libros;', capturado[0])
        self.assertIn('Se consultaron títulos', capturado[0])


if __name__ == '__main__':
    unittest.main()
