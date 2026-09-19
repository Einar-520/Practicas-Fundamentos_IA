"""Reglas y conexión de la práctica 9, compartidas por la web y Tkinter."""

from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure, OperationFailure, PyMongoError

from configuracion import cargar_configuracion

FILTRO = {"_id": "practica_09"}
PROYECCION = {"nombre": 1, "practica": 1, "dato": 1, "actualizado_en": 1}


def mensaje_error(error):
    """Traducir errores conocidos sin publicar la URI ni mensajes del driver."""
    if isinstance(error, OperationFailure):
        if error.code == 18:
            return "Atlas rechazó las credenciales. Revisa el usuario y la contraseña en tu .env."
        if error.code == 13:
            return "Faltan permisos. Pide al profesor acceso de lectura y escritura a tu base."
        return "Atlas rechazó la operación. Revisa los permisos con el profesor."
    if isinstance(error, ConfigurationError):
        return "No se pudo configurar Atlas. Revisa el dominio del clúster y la resolución DNS."
    if isinstance(error, ConnectionFailure):
        return "No hay comunicación con Atlas. Comprueba Internet y que tu IP esté autorizada."
    return "No se pudo completar la operación en MongoDB Atlas."


def serializar(documento):
    if documento is None:
        return None
    fecha = documento.get("actualizado_en")
    if isinstance(fecha, datetime):
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        fecha = fecha.isoformat()
    else:
        fecha = None
    return {"id": str(documento["_id"]),
            "nombre": str(documento.get("nombre", "")),
            "practica": 9, "dato": str(documento.get("dato", "")),
            "actualizado_en": fecha}


class ErrorAtlas(Exception):
    """Mensaje público controlado; nunca incluye la URI ni errores del driver."""

    def __init__(self, mensaje, codigo=503, guardado=False):
        super().__init__(mensaje)
        self.codigo = codigo
        self.guardado = guardado


def validar_dato(dato):
    if not isinstance(dato, str) or not 1 <= len(dato.strip()) <= 1000:
        raise ErrorAtlas("Escribe un dato de entre 1 y 1000 caracteres.", 400)
    return dato.strip()


class ServicioAtlas:
    def __init__(self, coleccion=None):
        self._coleccion = coleccion
        self._cliente = None
        self.base = "Einar_Ivan_Lazcano_Luna" if coleccion is not None else ""
        self.coleccion = "datos" if coleccion is not None else ""

    def abrir(self):
        """Conectar cuando se solicite una operación, sin escrituras automáticas."""
        if self._coleccion is not None:
            return
        try:
            mongo_url, self.base, self.coleccion = cargar_configuracion()
        except ValueError as error:
            raise ErrorAtlas(str(error)) from None
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

    def consultar(self):
        self.abrir()
        try:
            return serializar(self._coleccion.find_one(FILTRO, PROYECCION))
        except PyMongoError as error:
            raise ErrorAtlas(mensaje_error(error)) from None

    def guardar(self, dato):
        dato = validar_dato(dato)
        self.abrir()
        documento = {"nombre": "Einar Ivan Lazcano Luna", "practica": 9,
                     "dato": dato, "actualizado_en": datetime.now(timezone.utc)}
        try:
            resultado = self._coleccion.update_one(FILTRO, {"$set": documento}, upsert=True)
        except PyMongoError as error:
            raise ErrorAtlas(mensaje_error(error) +
                             " Consulta el documento antes de reintentar el guardado.") from None
        mensaje = ("Tu dato se guardó en Atlas." if resultado.upserted_id is not None
                   else "Tu dato se actualizó en Atlas.")
        try:
            guardado = self.consultar()
        except ErrorAtlas:
            raise ErrorAtlas("El guardado se confirmó, pero no se pudo consultar el resultado. Pulsa Actualizar.",
                             guardado=True) from None
        if guardado is None:
            raise ErrorAtlas("El guardado se confirmó, pero el documento ya no aparece. Pulsa Actualizar.",
                             guardado=True)
        return {"ok": True, "mensaje": mensaje, "documento": guardado}

    def cerrar(self):
        if self._cliente is not None:
            self._cliente.close()
            self._cliente = None
            self._coleccion = None
