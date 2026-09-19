"""Crear el .env de la práctica 10 sin mostrar ni publicar la contraseña."""

import os
from pathlib import Path
import tempfile
import warnings
from getpass import GetPassWarning, getpass

from dotenv import dotenv_values, set_key

from configuracion import ARCHIVO_ENV, cargar_configuracion

ENV_PRACTICA_9 = ARCHIVO_ENV.parent.parent / 'practica-09-conexion-mongodb-atlas' / '.env'


def crear_configuracion(destino=ARCHIVO_ENV, origen=None, solicitar_clave=getpass):
    destino = Path(destino)
    if destino.exists():
        cargar_configuracion(destino)
        return False
    valores = {
        'Mongo_User': 'hector1985',
        'Mongo_Password': '',
        'Mongo_Closter': 'utvt.qqqotrr.mongodb.net',
        'Mongo_DB': 'Einar_Ivan_Lazcano_Luna',
        'Mongo_Collection': 'climatizacion',
    }
    if origen is not None and Path(origen).is_file():
        # Reutilizar solo el acceso al clúster; la base y colección son de esta práctica.
        anteriores = dotenv_values(origen, interpolate=False)
        for clave in ('Mongo_User', 'Mongo_Password', 'Mongo_Closter'):
            valor = anteriores.get(clave)
            if not isinstance(valor, str) or not valor:
                raise ValueError('El .env de origen está incompleto. Corrígelo antes de reutilizarlo.')
            valores[clave] = valor
    else:
        with warnings.catch_warnings():
            warnings.simplefilter('error', GetPassWarning)
            valores['Mongo_Password'] = solicitar_clave('Contraseña del clúster del profesor (oculta): ')
        if not valores['Mongo_Password']:
            raise ValueError('La contraseña no puede estar vacía.')
    descriptor, nombre = tempfile.mkstemp(prefix='.env-', dir=destino.parent)
    os.close(descriptor)
    temporal = Path(nombre)
    try:
        for clave, valor in valores.items():
            set_key(temporal, clave, valor, quote_mode='always')
        cargar_configuracion(temporal)
        temporal.chmod(0o600)
        os.link(temporal, destino)  # Creación exclusiva: nunca sobrescribe otro .env.
    finally:
        temporal.unlink(missing_ok=True)
    return True


def main():
    try:
        creado = crear_configuracion(origen=ENV_PRACTICA_9)
    except GetPassWarning:
        print('Ejecuta este programa en la terminal WSL para introducir la contraseña de forma oculta.')
        return 1
    except ValueError as error:
        print(error)
        return 1
    except OSError:
        print('No se pudo crear o leer el .env. Revisa la carpeta y sus permisos.')
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\nConfiguración cancelada.')
        return 130
    if creado:
        print('Se creó el .env propio de la práctica 10, con la colección climatizacion.')
        if ENV_PRACTICA_9.is_file():
            print('Se reutilizó el acceso local de la práctica 9. Su archivo se conservó.')
    else:
        print('El .env de la práctica 10 ya existe y se conservó.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
