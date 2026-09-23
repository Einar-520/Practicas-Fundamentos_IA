"""Agente reactivo simple: percepción, decisión y registro de su acción."""

from datetime import datetime, timezone
from math import isfinite


ALUMNO = 'Einar Ivan Lazcano Luna'


class AgenteClimatizacion:
    def __init__(self):
        self.temperatura = 0.0
        self.humedad = 0.0
        self.accion = ''
        self._percibido = False

    def percibir(self, temperatura, humedad):
        """Recibir los datos del formulario y validar antes de cambiar el estado."""
        self._percibido = False
        self.accion = ''
        temperatura = self._leer_float(temperatura, 'temperatura')
        humedad = self._leer_float(humedad, 'humedad')
        if not 0 <= humedad <= 100:
            raise ValueError('La humedad debe estar entre 0 y 100 %.')
        self.temperatura, self.humedad = temperatura, humedad
        self._percibido = True

    def tomar_decision(self):
        """Aplicar las condiciones del profesor, conservando orden y límites."""
        if not self._percibido:
            raise ValueError('Primero ingresa una temperatura y una humedad válidas.')
        if self.temperatura > 30 and self.humedad > 70:
            self.accion = 'Encender aire acondicionado (Modo Deshumidificador)'
        elif self.temperatura > 30:
            self.accion = 'Encender ventilador'
        elif self.temperatura < 18:
            self.accion = 'Encender calefacción'
        else:
            self.accion = 'Mantener sistema apagado'
        return self.accion

    def mostrar_resultado(self):
        """Devolver el resumen para que la interfaz pueda mostrarlo."""
        if not self.accion:
            raise ValueError('Primero calcula la decisión del agente.')
        return (f'Percepción → Temp: {self.temperatura:g} °C | Humedad: {self.humedad:g} %\n'
                f'Acción → {self.accion}')

    def ejecutar(self, almacenamiento, identificador=None):
        """Crear o actualizar el registro con la acción recalculada por el agente."""
        self.tomar_decision()
        documento = {
            'practica': 10,
            'alumno': ALUMNO,
            'agente': type(self).__name__,
            'temperatura': self.temperatura,
            'humedad': self.humedad,
            'accion': self.accion,
            'fecha': datetime.now(timezone.utc),
        }
        if identificador is not None:
            return almacenamiento.actualizar(identificador, documento)
        return almacenamiento.insertar(documento)

    @staticmethod
    def _leer_float(valor, nombre):
        """Aceptar punto o coma decimal y rechazar texto, infinito y NaN."""
        try:
            if isinstance(valor, bool):
                raise ValueError
            if isinstance(valor, str):
                valor = valor.strip().replace(',', '.')
            numero = float(valor)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(f'Ingresa un número válido para la {nombre}.') from None
        if not isfinite(numero):
            raise ValueError(f'La {nombre} debe ser un número finito.')
        return numero
