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
