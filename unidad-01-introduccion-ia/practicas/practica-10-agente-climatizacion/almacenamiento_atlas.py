"""CRUD de los registros personales de la práctica 10 en MongoDB Atlas."""

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure, OperationFailure, PyMongoError

from agente_climatizacion import ACCIONES, ALUMNO
from configuracion import cargar_configuracion

CAMPOS = ('practica', 'alumno', 'agente', 'temperatura', 'humedad', 'accion', 'fecha')
PROYECCION = {campo: 1 for campo in (*CAMPOS, 'actualizado_en')}
FILTRO_BASE = {'practica': 10, 'alumno': ALUMNO}
TAMANO_PAGINA = 50


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
    if 'actualizado_en' in documento:
        resultado['actualizado_en'] = documento['actualizado_en']
    for campo in ('fecha', 'actualizado_en'):
        fecha = resultado.get(campo)
        if isinstance(fecha, datetime):
            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=timezone.utc)
            resultado[campo] = fecha.isoformat()
    return resultado


def filtro_registro(identificador):
    # Validar antes de conectar: nunca aceptar un filtro enviado como diccionario.
    if not isinstance(identificador, str) or not ObjectId.is_valid(identificador):
        raise ValueError('Selecciona un registro con un identificador válido de MongoDB.')
    return {**FILTRO_BASE, '_id': ObjectId(identificador)}


def filtro_consulta(accion=None):
    """Consultar una acción exacta sin aceptar filtros arbitrarios del usuario."""
    filtro = dict(FILTRO_BASE)
    if accion is not None:
        if not isinstance(accion, str) or accion not in ACCIONES:
            raise ValueError('Selecciona una de las cuatro acciones del agente.')
        filtro['accion'] = accion
    return filtro


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
        """Crear un documento nuevo por evaluación."""
        self.abrir()
        copia = {campo: documento[campo] for campo in CAMPOS}
        try:
            resultado = self._coleccion.insert_one(copia)
        except PyMongoError as error:
            raise ErrorAtlas(mensaje_error(error) +
                             ' La creación no se confirmó. Actualiza la lista antes de reintentar.') from None
        if not resultado.acknowledged:
            raise ErrorAtlas('La creación no se confirmó. Actualiza la lista antes de reintentar.')
        copia['_id'] = resultado.inserted_id
        return serializar(copia)

    def listar(self, pagina=0, accion=None):
        """Leer una página y comprobar si hay más resultados, sin contar toda la colección."""
        if type(pagina) is not int or pagina < 0:
            raise ValueError('La página debe ser un entero no negativo.')
        filtro = filtro_consulta(accion)
        self.abrir()
        try:
            cursor = (self._coleccion.find(filtro, PROYECCION)
                      .sort([('fecha', -1), ('_id', -1)])
                      .skip(pagina * TAMANO_PAGINA).limit(TAMANO_PAGINA + 1))
            documentos = list(cursor)
            return {'registros': [serializar(d) for d in documentos[:TAMANO_PAGINA]],
                    'hay_siguiente': len(documentos) > TAMANO_PAGINA, 'pagina': pagina}
        except PyMongoError as error:
            raise ErrorAtlas(mensaje_error(error)) from None

    def consultar_ultimo(self):
        """Mantener disponible la consulta individual de la versión anterior."""
        self.abrir()
        try:
            documento = self._coleccion.find_one(
                FILTRO_BASE, PROYECCION, sort=[('fecha', -1), ('_id', -1)])
            return serializar(documento)
        except PyMongoError as error:
            raise ErrorAtlas(mensaje_error(error)) from None

    def actualizar(self, identificador, documento):
        """Editar solo los valores del agente; conservar fecha inicial y campos ajenos."""
        filtro = filtro_registro(identificador)
        cambios = {campo: documento[campo] for campo in ('temperatura', 'humedad', 'accion')}
        cambios['actualizado_en'] = datetime.now(timezone.utc)
        self.abrir()
        try:
            resultado = self._coleccion.update_one(filtro, {'$set': cambios}, upsert=False)
        except PyMongoError as error:
            raise ErrorAtlas(mensaje_error(error) +
                             ' La actualización no se confirmó. Actualiza la lista antes de reintentar.') from None
        if not resultado.acknowledged:
            raise ErrorAtlas('La actualización no se confirmó. Actualiza la lista antes de reintentar.')
        if resultado.matched_count == 0:
            raise ErrorAtlas('El registro ya no existe o no pertenece a esta práctica y alumno. Actualiza la lista.')
        # La lectura posterior se hace por separado para no confundir un fallo
        # de consulta con una actualización que Atlas ya confirmó.
        return {'_id': identificador}

    def eliminar(self, identificador):
        """Eliminar exactamente el registro seleccionado de esta práctica y alumno."""
        filtro = filtro_registro(identificador)
        self.abrir()
        try:
            resultado = self._coleccion.delete_one(filtro)
        except PyMongoError as error:
            raise ErrorAtlas(mensaje_error(error) +
                             ' La eliminación no se confirmó. Actualiza la lista antes de reintentar.') from None
        if not resultado.acknowledged:
            raise ErrorAtlas('La eliminación no se confirmó. Actualiza la lista antes de reintentar.')
        if resultado.deleted_count == 0:
            raise ErrorAtlas('El registro ya no existe o no pertenece a esta práctica y alumno. Actualiza la lista.')
        return {'_id': identificador}

    def cerrar(self):
        if self._cliente is not None:
            self._cliente.close()
            self._cliente = None
            self._coleccion = None
