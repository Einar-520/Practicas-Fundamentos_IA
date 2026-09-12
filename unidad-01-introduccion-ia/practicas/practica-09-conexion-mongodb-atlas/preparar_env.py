"""Crear .env localmente, solicitando la contraseña de forma oculta."""

import os
import tempfile
import warnings
from getpass import GetPassWarning, getpass
from pathlib import Path

from dotenv import set_key

from configuracion import ARCHIVO_ENV, cargar_configuracion


def main():
    if ARCHIVO_ENV.exists():
        try:
            cargar_configuracion()
        except ValueError as error:
            print(error)
            print("Corrige tu .env en VS Code y vuelve a ejecutar este programa.")
            return 1
        print("El archivo .env ya existe y se conservó.")
        return 0

    try:
        print("Introduce la contraseña entregada por el profesor; no se mostrará al escribir.")
        with warnings.catch_warnings():
            warnings.simplefilter("error", GetPassWarning)
            contrasena = getpass("Mongo_Password: ")
        if not contrasena:
            print("La contraseña no puede estar vacía.")
            return 1
        valores = {
            "Mongo_User": "hector1985",
            "Mongo_Password": contrasena,
            "Mongo_Closter": "utvt.qqqotrr.mongodb.net",
            "Mongo_DB": "Einar_Ivan_Lazcano_Luna",
            "Mongo_Collection": "datos",
        }
        descriptor, nombre = tempfile.mkstemp(prefix=".env-", dir=ARCHIVO_ENV.parent)
        temporal = Path(nombre)
        os.close(descriptor)
        try:
            for clave, valor in valores.items():
                set_key(temporal, clave, valor, quote_mode="always")
            cargar_configuracion(temporal)
            os.chmod(temporal, 0o600)
            # La creación exclusiva evita sobrescribir una configuración existente.
            os.link(temporal, ARCHIVO_ENV)
        finally:
            temporal.unlink(missing_ok=True)
    except GetPassWarning:
        print("Ejecuta este programa en la terminal WSL para introducir la contraseña de forma oculta.")
        return 1
    except (OSError, ValueError):
        print("No se pudo crear .env. Revisa la carpeta y sus permisos.")
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nConfiguración cancelada.")
        return 130
    print("Archivo .env creado. La contraseña y el enlace completo no se muestran en pantalla.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
