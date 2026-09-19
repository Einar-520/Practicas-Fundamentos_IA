# Práctica 9: Tkinter, interfaz web y MongoDB Atlas

Programa independiente de la práctica 8. Aquí la conexión es al clúster del profesor.
Puedes usar una ventana de escritorio con Tkinter o la página web existente.
Ambas interfaces pertenecen a la misma práctica y utilizan servicio_atlas.py para
validar, guardar y consultar el mismo documento; no hay copias de las reglas.

## Abrir la ventana Tkinter en WSL

Guarda los archivos abiertos en VS Code. Desde la raíz del proyecto:

```bash
cd ~/universidad/fundamentos-ia
git pull --ff-only origin main
sudo apt update
sudo apt install -y python3-tk
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/requirements.txt
bash unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/ejecutar_tkinter.sh
```

El lanzador utiliza el intérprete .venv/bin/python del proyecto. Si todavía no
existe, créalo con python3 -m venv .venv antes de instalar las dependencias.
También puedes abrir interfaz_tkinter.py en VS Code y ejecutarlo seleccionando
ese intérprete. Se abre una ventana de escritorio; esta opción no necesita un
servidor Flask ni una dirección localhost.

La aplicación lee el mismo .env junto a configuracion.py. Si no existe, créalo
con preparar_env.py siguiendo el apartado de variables; no reemplaces uno existente.
Tkinter es un componente de Python instalado mediante el paquete del sistema,
no una dependencia de pip. Si utilizas otra versión de Python, instala el paquete
Tk correspondiente a ese intérprete.

WSL necesita soporte para aplicaciones gráficas (WSLg). Microsoft lo documenta
para WSL 2 en Windows 10 build 19044 o posterior y Windows 11. Para verificar la
ventana de prueba ejecuta .venv/bin/python -m tkinter. Si aparece un error de
pantalla, revisa WSLg; en PowerShell puedes comprobar wsl --status y actualizar
WSL con wsl --update. Guarda el trabajo antes de reiniciar WSL.

## Uso de la ventana

1. Al abrir, se consulta el documento existente; no se escribe automáticamente.
2. Escribe de 1 a 1000 caracteres y pulsa **Guardar en Atlas** o **Ctrl + Enter**.
3. El panel derecho muestra el documento consultado después del guardado.
4. **Actualizar consulta** vuelve a leer Atlas sin borrar el texto del formulario.
5. **Limpiar formulario** vacía únicamente el cuadro de entrada; no borra la base.

Cada guardado actualiza el documento _id: practica_09 y conserva los campos
ajenos al ejercicio. Las credenciales permanecen en el .env. La ventana muestra
solamente los nombres de la base y colección y los campos públicos del documento.

Las operaciones se ejecutan en un hilo de trabajo. La interfaz recibe los
resultados mediante una cola y after, siempre en el hilo principal de Tkinter.
Mientras hay una operación, se deshabilita otro envío. Si cierras la ventana
mientras guarda o consulta, espera a que termine para cerrar la conexión.
Los errores no borran lo escrito y marcan la última consulta como posiblemente
antigua. Un guardado confirmado cuya consulta posterior falla se indica
explícitamente; pulsa Actualizar antes de volver a guardar.

## Archivos

| Archivo | Función |
| --- | --- |
| `.env` | Usuario, contraseña, dominio, base y colección. Se crea únicamente en tu laptop. |
| `.env.example` | Ejemplo de configuración sin contraseña. |
| `configuracion.py` | Lee el .env y construye `mongo_url`. |
| `09_conexion_mongodb_atlas.py` | Servidor Flask y API web. |
| `interfaz_tkinter.py` | Ventana de escritorio, formulario y consulta del documento. |
| `servicio_atlas.py` | Conexión y reglas de guardado compartidas por ambas interfaces. |
| `ejecutar_tkinter.sh` | Abre la ventana con el Python del entorno .venv. |
| `tests/test_practica09.py` | Pruebas del servicio, API y flujo de la ventana con Atlas simulado. |
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

## Abrir la versión web en WSL

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

Para Tkinter se verificaron 11 pruebas del servicio, API y controlador: inserción,
actualización sin duplicados, validación, errores, reintento tras corregir la
configuración, cierre de conexión y trabajo de fondo sin envíos simultáneos.
La prueba de widgets reales se omite automáticamente si falta un servidor gráfico;
en el entorno de preparación no se pudo verificar visualmente la ventana.
Ejecuta las pruebas desde WSLg o un escritorio para incluir esa comprobación:

```bash
.venv/bin/python -m unittest discover -s unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/tests -v
```

## Referencias

- https://www.mongodb.com/docs/manual/reference/limits/
- https://www.mongodb.com/docs/atlas/security/add-ip-address-to-list/
- https://www.mongodb.com/docs/languages/python/pymongo-driver/current/databases-collections/
- https://bbc2.github.io/python-dotenv/
- https://flask.palletsprojects.com/en/stable/patterns/javascript/

- https://docs.python.org/3/library/tkinter.html
- https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps
