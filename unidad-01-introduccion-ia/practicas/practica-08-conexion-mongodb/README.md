# Práctica 8: Python, MongoDB y una página local

## Estructura

| Componente | Ubicación o función |
| --- | --- |
| Python + Flask | `08_conexion_mongodb.py`: formulario, validación y rutas. |
| PyMongo | Conexión y operaciones con el servidor local. |
| MongoDB Server | `mongodb://127.0.0.1:27017/`, en WSL. |
| Base de datos | `fundamentos_ia`. |
| Colección | `practicas`. |
| Interfaz | `templates/index.html` y `static/estilos.css`. |
| Compass | Aplicación independiente para consultar el mismo servidor. |

## Ejecutar desde WSL

Desde `~/universidad/fundamentos-ia`:

```bash
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-08-conexion-mongodb/requirements.txt
bash unidad-01-introduccion-ia/practicas/practica-08-conexion-mongodb/ejecutar.sh
```

Abre http://localhost:5000 en Windows. Mantén la terminal abierta. Detén Flask con Ctrl+C.
El servidor web escucha en 127.0.0.1, con depuración desactivada.

En VS Code selecciona Python: Select Interpreter y el intérprete
`/home/einar/universidad/fundamentos-ia/.venv/bin/python`.
Si `launch.json` define `python`, debe utilizar ese mismo intérprete.

## Guardar y consultar

El formulario comienza con número `8`, nombre `Conexión con MongoDB` y lenguaje `Python`.
Pulsa Guardar práctica. MongoDB crea la base y la colección en la primera escritura
si aún no existen. El número se guarda como `_id`: volver a usarlo actualiza ese
documento, conservando campos adicionales. Para crear otro documento, usa otro número.
Abrir la página no inserta datos. La tabla consulta hasta 100 documentos ordenados
por número; Actualizar vuelve a consultar. No hay operaciones de borrado.

Los datos se conservan en MongoDB al cerrar la página. Se validan el número positivo
y las longitudes de nombre (1–120) y lenguaje (1–40), también desde Python.
Las plantillas escapan HTML. El formulario usa un token de sesión y el cliente de
MongoDB se reutiliza y se cierra al terminar el proceso normalmente.

## Ver los datos en Compass

Conecta Compass al mismo servidor usando `mongodb://localhost:27017`.
En una configuración habitual de WSL, Windows puede acceder a servicios WSL por
localhost. Si Compass está en Windows y no conecta, confirma el reenvío de localhost
de WSL. Si conecta pero no aparecen los datos, comprueba que no esté accediendo a
otra instalación de MongoDB en Windows.

Selecciona `fundamentos_ia`, después `practicas` y actualiza la pestaña Documents.
Compass es un cliente visual: Python se conecta directamente a MongoDB Server.

## Problemas comunes

- `ModuleNotFoundError`: instala con `.venv/bin/python -m pip` y ejecuta con el mismo intérprete.
- MongoDB no disponible: verifica en WSL `mongosh --quiet --eval 'db.runCommand({ping: 1})'`.
- Puerto 5000 ocupado: detén la instancia anterior con Ctrl+C.
- El guardado perdió la conexión: consulta antes de reintentar; una pérdida de respuesta
  puede ocurrir después de que el servidor haya escrito el documento.

## Verificación de esta entrega

Se comprueban formulario, inserción/actualización, validación, escape HTML y errores
con el cliente de pruebas de Flask y una colección simulada. La conexión real al
servidor de tu laptop se comprueba al ejecutar esta entrega allí.

Documentación:
- https://flask.palletsprojects.com/en/stable/quickstart/
- https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/update/
- https://learn.microsoft.com/en-us/windows/wsl/networking
