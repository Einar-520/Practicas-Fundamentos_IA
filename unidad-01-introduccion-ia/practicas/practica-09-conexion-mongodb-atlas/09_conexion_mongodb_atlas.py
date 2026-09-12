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
