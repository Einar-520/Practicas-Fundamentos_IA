"""Inserción y consulta exclusivas de los registros de la práctica 10."""

from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure, OperationFailure, PyMongoError

from configuracion import cargar_configuracion

CAMPOS = ('practica', 'alumno', 'agente', 'temperatura', 'humedad', 'accion', 'fecha')
PROYECCION = {campo: 1 for campo in CAMPOS}


class ErrorAtlas(Exception):
    """Error público traducido, sin credenciales ni mensajes internos del driver."""


def mensaje_error(error):
    if isinstance(error, OperationFailure):
        if error.code == 18:
            return 'Atlas rechazó las credenciales. Revisa tu archivo .env.'
        if error.code == 13:
            return 'Faltan permisos. Pide al profesor acceso de lectura y escritura a tu base.'
        return 'Atlas rechazó la operación. Revisa los permisos y las reglas de la colección.'
    if isinstance(error, ConfigurationError):
        return 'No se pudo configurar Atlas. Revisa Mongo_Closter y la resolución DNS.'
    if isinstance(error, ConnectionFailure):
        return 'No hay comunicación con Atlas. Comprueba Internet y que tu IP esté autorizada.'
    return 'No se pudo completar la operación en MongoDB Atlas.'


def serializar(documento):
    if documento is None:
        return None
    resultado = {campo: documento.get(campo) for campo in CAMPOS}
    resultado['_id'] = str(documento['_id'])
    fecha = resultado['fecha']
    if isinstance(fecha, datetime):
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        resultado['fecha'] = fecha.isoformat()
    return resultado


class AlmacenamientoAtlas:
    def __init__(self, coleccion=None):
        self._coleccion = coleccion
        self._cliente = None
        self.base = 'Einar_Ivan_Lazcano_Luna' if coleccion is not None else ''
        self.coleccion = 'climatizacion' if coleccion is not None else ''

    def abrir(self):
        if self._coleccion is not None:
            return
        try:
            mongo_url, self.base, self.coleccion = cargar_configuracion()
        except (ValueError, OSError) as error:
            mensaje = str(error) if isinstance(error, ValueError) else 'No se pudo leer el archivo .env.'
            raise ErrorAtlas(mensaje) from None
        cliente = None
        try:
            cliente = MongoClient(mongo_url, serverSelectionTimeoutMS=10000,
                                  connectTimeoutMS=10000, socketTimeoutMS=10000,
                                  maxPoolSize=5, tz_aware=True)
            self._coleccion = cliente[self.base][self.coleccion]
            self._cliente = cliente
        except (PyMongoError, ValueError) as error:
            if cliente is not None:
                cliente.close()
            raise ErrorAtlas(mensaje_error(error)) from None

    def insertar(self, documento):
        """Crear un documento nuevo por evaluación, sin actualizar otros registros."""
        self.abrir()
        copia = {campo: documento[campo] for campo in CAMPOS}
        try:
            resultado = self._coleccion.insert_one(copia)
        except PyMongoError as error:
            raise ErrorAtlas(mensaje_error(error) +
                             ' El guardado no se confirmó. Consulta el último registro antes de reintentar.') from None
        if not resultado.acknowledged:
            raise ErrorAtlas('El guardado no se confirmó. Consulta el último registro antes de reintentar.')
        copia['_id'] = resultado.inserted_id
        return serializar(copia)

    def consultar_ultimo(self):
        self.abrir()
        try:
            documento = self._coleccion.find_one(
                {'practica': 10}, PROYECCION, sort=[('fecha', -1), ('_id', -1)])
            return serializar(documento)
        except PyMongoError as error:
            raise ErrorAtlas(mensaje_error(error)) from None

    def cerrar(self):
        if self._cliente is not None:
            self._cliente.close()
            self._cliente = None
            self._coleccion = None
