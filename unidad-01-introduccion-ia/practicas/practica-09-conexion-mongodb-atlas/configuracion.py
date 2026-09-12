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
