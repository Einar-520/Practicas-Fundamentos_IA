# Práctica 9: HTML, CSS, JavaScript, Python y MongoDB Atlas

Programa independiente de la práctica 8. Aquí la conexión es al clúster del profesor.

## Archivos

| Archivo | Función |
| --- | --- |
| `.env` | Usuario, contraseña, dominio, base y colección. Se crea únicamente en tu laptop. |
| `.env.example` | Ejemplo de configuración sin contraseña. |
| `configuracion.py` | Lee el .env y construye `mongo_url`. |
| `09_conexion_mongodb_atlas.py` | Servidor Flask, conexión y API para guardar y consultar. |
| `templates/index.html` | Estructura de la página y formulario. |
| `static/estilos.css` | Diseño adaptable a escritorio y móvil. |
| `static/app.js` | Guardado y consulta con fetch sin recargar, contador y estados. |
| `preparar_env.py` | Solicita la contraseña oculta y crea .env con permisos 600. |
| `requirements.txt` | Flask, PyMongo y python-dotenv. |
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

Abre http://localhost:5001 en el navegador. El puerto 5001 permite conservar
la práctica 8 en el puerto 5000. Mantén la terminal abierta y detén el servidor
con Ctrl+C. El servidor escucha en 127.0.0.1 con el depurador desactivado.

Escribe el dato en el formulario y pulsa Guardar en Atlas. El servidor escribe
solamente en la base y colección indicadas en .env. El documento conserva
`_id: practica_09`: cada guardado actualiza ese documento, sin duplicarlo.
El dato debe tener entre 1 y 1000 caracteres después de quitar espacios de los
extremos. La validación se realiza también en Python. No elimina documentos.
La base y colección se crean en la primera escritura. Abrir la página solamente
consulta. El botón Actualizar vuelve a leer el documento sin modificar el texto
que estés escribiendo. Ver documento JSON muestra los campos del documento.

Si la conexión se pierde después de confirmar la escritura, la página diferencia
ese caso de un guardado no confirmado. Pulsa Actualizar antes de reintentar.
Tras un error, la última consulta visible se identifica como posiblemente antigua.
No se configura ninguna escritura automática ni reintento de la interfaz.

## Arquitectura y credenciales

El navegador envía el formulario a Flask mediante fetch. Python construye
`mongo_url` y usa PyMongo para comunicarse con Atlas. La respuesta es JSON con el
documento; JavaScript lo muestra mediante textContent. La contraseña, el usuario
de acceso y la URI completa no se incluyen en HTML, JavaScript ni respuestas JSON.
Los nombres de base y colección sí se muestran como información de la práctica.
`.env` no se publica como archivo estático. El formulario incorpora un token CSRF.

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
Se prueban además los endpoints web con una colección simulada y la sintaxis de
JavaScript. El navegador del entorno de preparación bloquea las direcciones locales,
por lo que no se ha confirmado visualmente el diseño en ese navegador.
La ejecución en tu laptop confirma los permisos y la creación real de la base.

## Referencias

- https://www.mongodb.com/docs/manual/reference/limits/
- https://www.mongodb.com/docs/atlas/security/add-ip-address-to-list/
- https://www.mongodb.com/docs/languages/python/pymongo-driver/current/databases-collections/
- https://bbc2.github.io/python-dotenv/
- https://flask.palletsprojects.com/en/stable/patterns/javascript/
