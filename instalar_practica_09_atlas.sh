#!/usr/bin/env bash
# Instala la práctica 9. La contraseña se introduce localmente, nunca está en este instalador.
set -euo pipefail
proyecto="${1:-$HOME/universidad/fundamentos-ia}"
cd -- "$proyecto"
proyecto="$PWD"
practicas="$proyecto/unidad-01-introduccion-ia/practicas"
destino="$practicas/practica-09-conexion-mongodb-atlas"
[[ -d "$practicas" ]] || { echo "No se encontró la carpeta de prácticas en $proyecto"; exit 1; }
[[ ! -L "$destino" && ! -L "$destino/.env" ]] || { echo "El destino o .env es un enlace simbólico. Revisa la ruta."; exit 1; }
preparada="$(mktemp -d "$practicas/.practica-09-preparada-XXXXXX")"
respaldo=""
anterior_movida=0
instalada=0
limpiar() {
  codigo=$?
  if [[ "$anterior_movida" == 1 && "$instalada" == 0 && ! -e "$destino" ]]; then
    mv -- "$respaldo/practica-09-conexion-mongodb-atlas" "$destino" || echo "Recupera la versión anterior desde: $respaldo"
  fi
  if [[ -d "$preparada" ]]; then rm -rf -- "$preparada"; fi
  exit "$codigo"
}
trap limpiar EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
cat > "$preparada/09_conexion_mongodb_atlas.py" <<'FIN_ARCHIVO_PRACTICA09'
"""Práctica 9: crear la base personal en Atlas mediante una primera escritura."""

import json
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure, OperationFailure, PyMongoError

from configuracion import cargar_configuracion


def pedir_dato():
    while True:
        dato = input("Escribe el dato que deseas guardar: ").strip()
        if 1 <= len(dato) <= 1000:
            return dato
        print("Escribe un dato de entre 1 y 1000 caracteres.")


def main():
    print("=== Práctica 9: conexión con MongoDB Atlas ===")
    try:
        # mongo_url se genera con las cinco variables del archivo .env.
        mongo_url, mongo_db, mongo_collection = cargar_configuracion()
        print(f"Base de datos: {mongo_db}")
        print(f"Colección: {mongo_collection}")
        dato = pedir_dato()

        with MongoClient(mongo_url, serverSelectionTimeoutMS=10000,
                         connectTimeoutMS=10000, socketTimeoutMS=10000,
                         maxPoolSize=5) as cliente:
            cliente.admin.command("ping")
            print("Conexión con Atlas establecida.")

            base_datos = cliente[mongo_db]
            coleccion = base_datos[mongo_collection]
            filtro = {"_id": "practica_09"}
            documento = {
                "nombre": "Einar Ivan Lazcano Luna",
                "practica": 9,
                "dato": dato,
                "actualizado_en": datetime.now(timezone.utc),
            }
            # La primera escritura crea la base y la colección si aún no existen.
            resultado = coleccion.update_one(filtro, {"$set": documento}, upsert=True)
            if resultado.upserted_id is not None:
                print("Documento creado correctamente.")
            else:
                print("Documento de la práctica actualizado correctamente.")

            guardado = coleccion.find_one(filtro)
            if guardado is None:
                print("No se encontró el documento al consultarlo.")
                return 1
            print("\nDocumento recuperado desde Atlas:")
            print(json.dumps(guardado, ensure_ascii=False, indent=4, default=str))

    except (ValueError, ConfigurationError) as error:
        # Los errores del driver pueden contener información de la conexión.
        if isinstance(error, ConfigurationError):
            print("Revisa el dominio de Mongo_Closter y la resolución DNS de tu conexión.")
        else:
            print(error)
        return 1
    except OperationFailure as error:
        if error.code == 18:
            print("Atlas rechazó las credenciales. Revisa Mongo_User y Mongo_Password.")
        elif error.code == 13:
            print("El usuario no tiene permisos suficientes sobre esta base de datos.")
            print("Pide al profesor acceso de lectura y escritura a tu base.")
        else:
            print("Atlas rechazó la operación. Revisa los permisos y la configuración con el profesor.")
        return 1
    except ConnectionFailure:
        print("No se pudo completar la comunicación con Atlas.")
        print("Comprueba Internet, el dominio del clúster y que tu IP esté autorizada en Atlas.")
        print("Si la conexión se perdió durante el guardado, consulta el documento antes de reintentar.")
        return 1
    except PyMongoError:
        print("No se pudo completar la operación en MongoDB Atlas.")
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nOperación cancelada.")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
FIN_ARCHIVO_PRACTICA09
cat > "$preparada/configuracion.py" <<'FIN_ARCHIVO_PRACTICA09'
"""Leer .env y construir la variable mongo_url sin mostrar credenciales."""

import re
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import dotenv_values

ARCHIVO_ENV = Path(__file__).resolve().parent / ".env"


def cargar_configuracion(archivo=ARCHIVO_ENV):
    if not Path(archivo).is_file():
        raise ValueError("Falta el archivo .env. Ejecuta preparar_env.py primero.")
    # La configuración procede de este .env. No se expanden expresiones ${...}.
    valores = dotenv_values(archivo, interpolate=False)
    nombres = ("Mongo_User", "Mongo_Password", "Mongo_Closter", "Mongo_DB", "Mongo_Collection")
    if any(not isinstance(valores.get(nombre), str) or not valores[nombre] for nombre in nombres):
        raise ValueError("Completa las cinco variables de MongoDB en el archivo .env.")

    usuario = valores["Mongo_User"].strip()
    contrasena = valores["Mongo_Password"]
    cluster = valores["Mongo_Closter"].strip()
    base = valores["Mongo_DB"].strip()
    coleccion = valores["Mongo_Collection"].strip()
    if not usuario:
        raise ValueError("Mongo_User no puede estar vacío.")
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.mongodb\.net", cluster):
        raise ValueError("Mongo_Closter debe ser el dominio de Atlas, sin protocolo ni barras.")
    if not base or len(base.encode("utf-8")) >= 64 or any(c in base for c in '\\/. "$\x00'):
        raise ValueError("Mongo_DB debe tener menos de 64 bytes y no contener espacios, barras, puntos, comillas ni $.")
    if (not coleccion or "$" in coleccion or "\x00" in coleccion
            or coleccion.startswith("system.") or ".system." in coleccion
            or len(f"{base}.{coleccion}".encode("utf-8")) > 235):
        raise ValueError("Mongo_Collection contiene un nombre no permitido o demasiado largo.")

    mongo_url = (
        f"mongodb+srv://{quote_plus(usuario)}:{quote_plus(contrasena)}@{cluster}/"
        f"{quote_plus(base)}?retryWrites=true&w=majority&authSource=admin&appName=Practica09"
    )
    return mongo_url, base, coleccion
FIN_ARCHIVO_PRACTICA09
cat > "$preparada/preparar_env.py" <<'FIN_ARCHIVO_PRACTICA09'
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
FIN_ARCHIVO_PRACTICA09
cat > "$preparada/.env.example" <<'FIN_ARCHIVO_PRACTICA09'
Mongo_User='hector1985'
Mongo_Password=''
Mongo_Closter='utvt.qqqotrr.mongodb.net'
Mongo_DB='Einar_Ivan_Lazcano_Luna'
Mongo_Collection='datos'
FIN_ARCHIVO_PRACTICA09
cat > "$preparada/.gitignore" <<'FIN_ARCHIVO_PRACTICA09'
.env
.env.*
.env-*
!.env.example
__pycache__/
*.pyc
FIN_ARCHIVO_PRACTICA09
cat > "$preparada/requirements.txt" <<'FIN_ARCHIVO_PRACTICA09'
pymongo>=4.6,<5
python-dotenv>=1,<2
FIN_ARCHIVO_PRACTICA09
cat > "$preparada/ejecutar.sh" <<'FIN_ARCHIVO_PRACTICA09'
#!/usr/bin/env bash
set -euo pipefail
directorio="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
proyecto="$(cd -- "$directorio/../../.." && pwd)"
exec "$proyecto/.venv/bin/python" "$directorio/09_conexion_mongodb_atlas.py"
FIN_ARCHIVO_PRACTICA09
cat > "$preparada/README.md" <<'FIN_ARCHIVO_PRACTICA09'
# Práctica 9: configuración .env y conexión con MongoDB Atlas

Programa independiente de la práctica 8. Aquí la conexión es al clúster del profesor.

## Archivos

| Archivo | Función |
| --- | --- |
| `.env` | Usuario, contraseña, dominio, base y colección. Se crea únicamente en tu laptop. |
| `.env.example` | Ejemplo de configuración sin contraseña. |
| `configuracion.py` | Lee el .env y construye `mongo_url`. |
| `09_conexion_mongodb_atlas.py` | Conecta, guarda un dato y consulta el documento. |
| `preparar_env.py` | Solicita la contraseña oculta y crea .env con permisos 600. |
| `requirements.txt` | PyMongo y python-dotenv. |
| `ejecutar.sh` | Ejecuta con el Python de .venv del proyecto. |

## Variables

```dotenv
Mongo_User='hector1985'
Mongo_Password=''
Mongo_Closter='utvt.qqqotrr.mongodb.net'
Mongo_DB='Einar_Ivan_Lazcano_Luna'
Mongo_Collection='datos'
```

La contraseña real se solicita en la terminal mediante `preparar_env.py`.
Se conserva `Mongo_Closter` como nombre de variable indicado en el enunciado.
MongoDB no permite espacios en los nombres de bases: por eso se usan guiones bajos.
El documento mantiene el nombre completo con espacios.
La colección es un contenedor llamado `datos`; el dato es el contenido del documento.

## Ejecutar en WSL

Desde `~/universidad/fundamentos-ia`:

```bash
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/requirements.txt
.venv/bin/python unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/preparar_env.py
bash unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/ejecutar.sh
```

El programa solicita el dato que deseas guardar y escribe solamente en la base y
colección indicadas en .env. El documento usa `_id: practica_09`: una segunda
ejecución actualiza ese documento, sin duplicarlo. No elimina documentos.
La base y la colección se crean en la primera escritura, no por construir la URL
ni por hacer ping. Se muestra el resultado de una consulta después de guardar.

## Construcción del enlace

El enlace se construye en memoria con este formato, nunca se imprime completo:

```text
mongodb+srv://<usuario>:<contraseña-codificada>@<clúster>/<base>?retryWrites=true&w=majority&authSource=admin&appName=Practica09
```

`quote_plus` codifica los caracteres especiales del usuario y la contraseña.
La conexión SRV activa TLS; la verificación de certificados permanece habilitada.
La colección se selecciona con `cliente[mongo_db][mongo_collection]`, por lo que
no se añade como segmento adicional a la URI.

El archivo .env se lee por su ruta junto a configuracion.py, independientemente
del directorio desde el que ejecutes el programa. No se interpretan expresiones
`${...}` dentro de la contraseña. Los mensajes del driver no se imprimen con la URI.

## Acceso a Atlas

El profesor debe autorizar tu IP pública en Network Access y conceder al usuario
permisos de lectura y escritura sobre `Einar_Ivan_Lazcano_Luna`. Si no cuentas con
permisos administrativos, solicita al profesor esos cambios. El script no modifica
usuarios, permisos, listas de IP ni otras bases del clúster.

Para comprobarlo visualmente, el profesor puede consultar esa base en Atlas.
También puedes usar Compass con el host de Atlas y sus campos de autenticación.
Si guardaste en Atlas, los datos no aparecerán en la conexión local de la práctica 8.

## Git

`.env` queda excluido mediante .gitignore; `.env.example` sí puede subirse.
Desde el proyecto, comprueba la regla con:

```bash
git check-ignore unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/.env
```

No compartas el .env ni una URL completa que contenga la contraseña.

## Validación de la entrega

Se verifican la lectura del .env, codificación de credenciales con valores ficticios,
validación de nombres y el flujo de guardado con una conexión simulada. No se prueba
la contraseña ni se escribe en el clúster del profesor desde el entorno de preparación.
La ejecución en tu laptop confirma los permisos y la creación real de la base.

## Referencias

- https://www.mongodb.com/docs/manual/reference/limits/
- https://www.mongodb.com/docs/atlas/security/add-ip-address-to-list/
- https://www.mongodb.com/docs/languages/python/pymongo-driver/current/databases-collections/
- https://bbc2.github.io/python-dotenv/
FIN_ARCHIVO_PRACTICA09

if [[ -f "$destino/.env" ]]; then
  install -m 600 -- "$destino/.env" "$preparada/.env"
fi
if [[ ! -x "$proyecto/.venv/bin/python" ]]; then
  python3 -m venv "$proyecto/.venv"
fi
"$proyecto/.venv/bin/python" -m pip install -r "$preparada/requirements.txt"
"$proyecto/.venv/bin/python" -c 'import ast, sys; from pathlib import Path; [ast.parse(p.read_text()) for p in Path(sys.argv[1]).glob("*.py")]; import dotenv, pymongo; print("PyMongo y python-dotenv disponibles.")' "$preparada"
if [[ -e "$destino" ]]; then
  carpeta_respaldos="$(dirname -- "$proyecto")/$(basename -- "$proyecto")-respaldos"
  mkdir -p -- "$carpeta_respaldos"
  respaldo="$(mktemp -d "$carpeta_respaldos/practica-09-XXXXXX")"
  mv -- "$destino" "$respaldo/practica-09-conexion-mongodb-atlas"
  anterior_movida=1
fi
mv -- "$preparada" "$destino"
instalada=1
echo "Práctica 9 instalada en: $destino"
if [[ -n "$respaldo" ]]; then echo "Versión anterior guardada en: $respaldo"; fi
"$proyecto/.venv/bin/python" "$destino/preparar_env.py"
echo "Ahora puedes ejecutar, desde la raíz del proyecto:"
echo "bash unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/ejecutar.sh"
