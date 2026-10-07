"""Persistencia con ámbito fijo, bajas lógicas, historial y control de versiones."""
import copy
import json
import threading
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlsplit
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError, DuplicateKeyError

COLECCIONES = ('camiones', 'accesos', 'incidentes', 'riesgos_eticos', 'evaluaciones_llm')
AMBITO = {'proyecto': 'examen_llm_logistica', 'alumno': 'Einar_Ivan_Lazcano_Luna'}


class ErrorDatos(RuntimeError):
    pass


def ahora():
    return datetime.now(timezone.utc)


def serializable(valor):
    if isinstance(valor, dict):
        return {k: serializable(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [serializable(v) for v in valor]
    if isinstance(valor, datetime):
        return valor.astimezone(timezone.utc).isoformat()
    return valor


def fecha(valor):
    return datetime.fromisoformat(valor.replace('Z', '+00:00')) if isinstance(valor, str) else valor


def rango_fechas(desde='', hasta=''):
    try:
        inicio = datetime.strptime(desde, '%Y-%m-%d').replace(tzinfo=timezone.utc) if desde else None
        fin = datetime.strptime(hasta, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1) if hasta else None
    except ValueError:
        raise ValueError('Las fechas deben tener formato AAAA-MM-DD.') from None
    if inicio and fin and inicio >= fin:
        raise ValueError('La fecha inicial debe ser anterior o igual a la final.')
    return inicio, fin


def preparar(datos, operador, anterior=None, motivo='Alta'):
    datos = copy.deepcopy(datos)
    reservados = {'_id', 'version', 'creado_en', 'actualizado_en', 'historico', 'eliminado', *AMBITO}
    if reservados & datos.keys():
        raise ValueError('El formulario contiene campos internos no editables.')
    evento = {'fecha': ahora().isoformat(), 'operador': operador, 'motivo': motivo,
              'anterior': {k: v for k, v in (anterior or {}).items() if k not in reservados}}
    return datos, evento


class MongoRepositorio:
    modo = 'MongoDB'

    def __init__(self, uri, base, cliente=None):
        try:
            self.cliente = cliente if cliente is not None else MongoClient(
                uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000,
                socketTimeoutMS=15000, tz_aware=True, appname='ExamenLogiSmart')
            self.db = self.cliente[base]
            self.origen = {'tipo': 'mongodb', 'base': base,
                           'servidor': urlsplit(uri).hostname or 'MongoDB'}
        except PyMongoError:
            raise ErrorDatos('Configuración de MongoDB inválida. Revisa el archivo .env.') from None

    def _coleccion(self, nombre):
        if nombre not in COLECCIONES:
            raise ValueError('Colección no permitida.')
        return self.db[nombre]

    def comprobar(self):
        try:
            self.cliente.admin.command('ping')
            for campo in ('placa', 'camion_id'):
                self.db.camiones.create_index(
                    [('proyecto', 1), ('alumno', 1), (campo, 1)], unique=True,
                    partialFilterExpression={**AMBITO, 'eliminado': False},
                    name=f'examen_unico_{campo}')
            return 'Conexión a MongoDB correcta.'
        except PyMongoError:
            raise ErrorDatos('No se pudo conectar o preparar MongoDB. Revisa servidor, permisos, usuario y acceso de red de Atlas.') from None

    def listar(self, nombre, filtro=None, desde='', hasta=''):
        inicio, fin = rango_fechas(desde, hasta)
        consulta = {**(filtro or {}), **AMBITO, 'eliminado': False}
        if inicio or fin:
            consulta['creado_en'] = {}
            if inicio: consulta['creado_en']['$gte'] = inicio
            if fin: consulta['creado_en']['$lt'] = fin
        try:
            return [serializable(d) for d in self._coleccion(nombre).find(consulta).sort('creado_en', -1)]
        except PyMongoError:
            raise ErrorDatos('No se pudieron consultar los registros de MongoDB. Revisa la conexión.') from None

    def obtener(self, nombre, identificador):
        datos = self.listar(nombre, {'_id': identificador})
        if not datos:
            raise ErrorDatos('El registro ya no está disponible. Actualiza la lista.')
        return datos[0]

    def contar(self, nombre, filtro=None):
        """Cuenta solamente los documentos activos de este alumno y proyecto."""
        try:
            return self._coleccion(nombre).count_documents({**(filtro or {}), **AMBITO, 'eliminado': False})
        except PyMongoError:
            raise ErrorDatos('No se pudieron consultar los registros. Revisa la conexión y los permisos de MongoDB.') from None

    def crear(self, nombre, datos, operador):
        datos, evento = preparar(datos, operador)
        documento = {**datos, **AMBITO, '_id': uuid4().hex, 'eliminado': False,
                     'version': 1, 'creado_en': ahora(), 'actualizado_en': ahora(), 'historico': [evento]}
        try:
            resultado = self._coleccion(nombre).insert_one(documento)
            if not resultado.acknowledged:
                raise ErrorDatos('MongoDB no confirmó la escritura. Consulta la lista antes de repetirla.')
            return serializable(documento)
        except DuplicateKeyError:
            raise ErrorDatos('Ya existe un camión con esa placa o identificador.') from None
        except PyMongoError:
            raise ErrorDatos('MongoDB no confirmó el guardado. Consulta los registros antes de volver a intentarlo.') from None

    def actualizar(self, nombre, identificador, datos, operador, version, motivo):
        anterior = self.obtener(nombre, identificador)
        datos, evento = preparar(datos, operador, anterior, motivo)
        consulta = {**AMBITO, '_id': identificador, 'version': version, 'eliminado': False}
        try:
            documento = self._coleccion(nombre).find_one_and_update(
                consulta, {'$set': {**datos, 'actualizado_en': ahora()},
                           '$inc': {'version': 1}, '$push': {'historico': evento}},
                return_document=ReturnDocument.AFTER)
            if documento is None:
                raise ErrorDatos('Otro operador modificó el registro. Actualiza antes de guardar.')
            return serializable(documento)
        except DuplicateKeyError:
            raise ErrorDatos('Ya existe un camión con esa placa o identificador.') from None
        except PyMongoError:
            raise ErrorDatos('MongoDB no confirmó la actualización. Consulta el registro antes de repetirla.') from None

    def eliminar(self, nombre, identificador, operador, version):
        # Baja lógica: conserva la evidencia de accesos, incidentes y evaluaciones.
        try:
            resultado = self._coleccion(nombre).update_one(
                {**AMBITO, '_id': identificador, 'version': version, 'eliminado': False},
                {'$set': {'eliminado': True, 'actualizado_en': ahora()}, '$inc': {'version': 1},
                 '$push': {'historico': {'fecha': ahora().isoformat(), 'operador': operador, 'motivo': 'Baja lógica'}}})
            if resultado.matched_count != 1:
                raise ErrorDatos('El registro cambió o ya se eliminó. Actualiza la lista.')
        except PyMongoError:
            raise ErrorDatos('No se pudo confirmar la baja. Consulta los registros antes de repetirla.') from None

    def agregar_incidentes(self, desde='', hasta=''):
        inicio, fin = rango_fechas(desde, hasta)
        filtro = {**AMBITO, 'eliminado': False}
        if inicio or fin:
            filtro['creado_en'] = {}
            if inicio: filtro['creado_en']['$gte'] = inicio
            if fin: filtro['creado_en']['$lt'] = fin
        pipeline = [
            {'$match': filtro},
            {'$group': {'_id': {'categoria': '$clasificacion.categoria',
                                'anio': {'$isoWeekYear': '$creado_en'},
                                'semana': {'$isoWeek': '$creado_en'}}, 'total': {'$sum': 1}}},
            {'$sort': {'_id.anio': 1, '_id.semana': 1, '_id.categoria': 1}},
        ]
        try:
            return [{**d['_id'], 'total': d['total']} for d in self.db.incidentes.aggregate(pipeline)]
        except PyMongoError:
            raise ErrorDatos('No se pudo ejecutar la agregación de incidentes por categoría y semana.') from None

    def cerrar(self):
        self.cliente.close()


class DemoRepositorio:
    """Adaptador local explícito para ensayar; no sustituye la validación de MongoDB."""
    modo = 'DEMOSTRACIÓN LOCAL (JSON)'

    def __init__(self, ruta: Path):
        self.ruta, self.lock = ruta, threading.RLock()
        self.origen = {'tipo': 'demo', 'base': ruta.name, 'servidor': 'Archivo local'}
        self.datos = {c: [] for c in COLECCIONES}
        if ruta.exists():
            try:
                datos = json.loads(ruta.read_text(encoding='utf-8'))
                if set(datos) != set(COLECCIONES) or any(not isinstance(v, list) for v in datos.values()):
                    raise ValueError
                self.datos = datos
            except (OSError, ValueError):
                raise ErrorDatos('No se pudo leer la base de demostración. Conserva el archivo y revisa su formato.') from None

    def _guardar(self):
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = self.ruta.with_suffix('.tmp')
        temporal.write_text(json.dumps(serializable(self.datos), ensure_ascii=False, indent=2), encoding='utf-8')
        temporal.replace(self.ruta)

    def comprobar(self):
        return 'Modo de demostración local. MongoDB no está conectado.'

    def contar(self, nombre, filtro=None):
        return len(self.listar(nombre, filtro))

    def listar(self, nombre, filtro=None, desde='', hasta=''):
        inicio, fin = rango_fechas(desde, hasta)
        with self.lock:
            resultado = []
            for d in self.datos[nombre]:
                if d['eliminado'] or any(d.get(k) != v for k, v in (filtro or {}).items()):
                    continue
                f = fecha(d['creado_en'])
                if (inicio and f < inicio) or (fin and f >= fin):
                    continue
                resultado.append(copy.deepcopy(d))
            return sorted(resultado, key=lambda d: d['creado_en'], reverse=True)

    def obtener(self, nombre, identificador):
        resultado = self.listar(nombre, {'_id': identificador})
        if not resultado:
            raise ErrorDatos('El registro ya no está disponible. Actualiza la lista.')
        return resultado[0]

    def _unico(self, nombre, datos, excluir=None):
        if nombre == 'camiones':
            for d in self.listar(nombre):
                if d['_id'] != excluir and any(d[k] == datos.get(k, d[k]) for k in ('placa', 'camion_id')):
                    raise ErrorDatos('Ya existe un camión con esa placa o identificador.')

    def crear(self, nombre, datos, operador):
        with self.lock:
            datos, evento = preparar(datos, operador)
            self._unico(nombre, datos)
            documento = {**datos, **AMBITO, '_id': uuid4().hex, 'eliminado': False,
                         'version': 1, 'creado_en': ahora().isoformat(), 'actualizado_en': ahora().isoformat(), 'historico': [evento]}
            self.datos[nombre].append(documento)
            try:
                self._guardar()
            except OSError:
                self.datos[nombre].pop()
                raise ErrorDatos('No se pudo guardar la base de demostración.') from None
            return copy.deepcopy(documento)

    def actualizar(self, nombre, identificador, datos, operador, version, motivo):
        with self.lock:
            anterior = self.obtener(nombre, identificador)
            if anterior['version'] != version:
                raise ErrorDatos('El registro cambió; actualiza antes de guardar.')
            datos, evento = preparar(datos, operador, anterior, motivo)
            self._unico(nombre, {**anterior, **datos}, identificador)
            nuevo = {**anterior, **datos, 'version': version + 1, 'actualizado_en': ahora().isoformat(),
                     'historico': anterior['historico'] + [evento]}
            self._sustituir(nombre, identificador, nuevo)
            return copy.deepcopy(nuevo)

    def _sustituir(self, nombre, identificador, nuevo):
        indice = next(i for i, d in enumerate(self.datos[nombre]) if d['_id'] == identificador)
        anterior = self.datos[nombre][indice]
        self.datos[nombre][indice] = nuevo
        try:
            self._guardar()
        except OSError:
            self.datos[nombre][indice] = anterior
            raise ErrorDatos('No se pudo actualizar la base de demostración.') from None

    def eliminar(self, nombre, identificador, operador, version):
        with self.lock:
            anterior = self.obtener(nombre, identificador)
            if anterior['version'] != version:
                raise ErrorDatos('El registro cambió; actualiza antes de eliminar.')
            nuevo = {**anterior, 'eliminado': True, 'version': version + 1, 'actualizado_en': ahora().isoformat(),
                     'historico': anterior['historico'] + [{'fecha': ahora().isoformat(), 'operador': operador, 'motivo': 'Baja lógica'}]}
            self._sustituir(nombre, identificador, nuevo)

    def agregar_incidentes(self, desde='', hasta=''):
        contador = Counter()
        for d in self.listar('incidentes', desde=desde, hasta=hasta):
            anio, semana, _ = fecha(d['creado_en']).isocalendar()
            contador[(anio, semana, d['clasificacion']['categoria'])] += 1
        return [{'anio': a, 'semana': s, 'categoria': c, 'total': total} for (a, s, c), total in sorted(contador.items())]

    def cerrar(self):
        pass
