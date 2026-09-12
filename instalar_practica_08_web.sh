#!/usr/bin/env bash
# Instala exclusivamente la práctica 8 y conserva la versión anterior.
set -euo pipefail
proyecto="${1:-$HOME/universidad/fundamentos-ia}"
cd -- "$proyecto"
proyecto="$PWD"
practicas="$proyecto/unidad-01-introduccion-ia/practicas"
destino="$practicas/practica-08-conexion-mongodb"
[[ -d "$practicas" ]] || { echo "No se encontró la carpeta de prácticas en $proyecto"; exit 1; }
[[ ! -L "$destino" ]] || { echo "La carpeta de destino es un enlace simbólico. Revisa la ruta."; exit 1; }
preparada="$(mktemp -d "$practicas/.practica-08-preparada-XXXXXX")"
respaldo=""
anterior_movida=0
instalada=0
limpiar() {
  codigo=$?
  if [[ "$anterior_movida" == 1 && "$instalada" == 0 && ! -e "$destino" ]]; then
    mv -- "$respaldo/practica-08-conexion-mongodb" "$destino" || echo "Recupera la versión anterior desde: $respaldo"
  fi
  if [[ -d "$preparada" ]]; then rm -rf -- "$preparada"; fi
  exit "$codigo"
}
trap limpiar EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir -p -- "$preparada/templates" "$preparada/static"
cat > "$preparada/08_conexion_mongodb.py" <<'FIN_ARCHIVO_PRACTICA08'
"""Práctica 8: interfaz web local para guardar y consultar en MongoDB."""

import atexit
import re
import secrets
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

URI_MONGODB = "mongodb://127.0.0.1:27017/"
BASE_DATOS = "fundamentos_ia"
COLECCION = "practicas"
DIRECTORIO = Path(__file__).resolve().parent


def validar(datos):
    """Validar también en Python, aunque el navegador valide el formulario."""
    numero = datos["numero"]
    if not re.fullmatch(r"[0-9]{1,19}", numero):
        raise ValueError("El número debe ser un entero positivo.")
    numero = int(numero)
    if not 1 <= numero <= 9223372036854775807:
        raise ValueError("El número está fuera del rango permitido.")
    if not 1 <= len(datos["nombre"]) <= 120:
        raise ValueError("Escribe un nombre de entre 1 y 120 caracteres.")
    if not 1 <= len(datos["lenguaje"]) <= 40:
        raise ValueError("Escribe un lenguaje de entre 1 y 40 caracteres.")
    return numero, {"nombre": datos["nombre"], "lenguaje": datos["lenguaje"]}


def crear_app(coleccion=None):
    app = Flask(__name__, template_folder=str(DIRECTORIO / "templates"),
                static_folder=str(DIRECTORIO / "static"))
    app.config.update(SECRET_KEY=secrets.token_hex(32), MAX_CONTENT_LENGTH=16384,
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

    if coleccion is None:
        cliente = MongoClient(URI_MONGODB, serverSelectionTimeoutMS=3000,
                              connectTimeoutMS=3000, socketTimeoutMS=3000)
        atexit.register(cliente.close)
        coleccion = cliente[BASE_DATOS][COLECCION]

    def pagina(datos=None, error=None, estado=200):
        session.setdefault("csrf", secrets.token_hex(32))
        try:
            registros = list(coleccion.find({}, {"nombre": 1, "lenguaje": 1})
                             .sort("_id", 1).limit(100))
            conectado = True
        except PyMongoError:
            registros, conectado = [], False
            error = error or "No se pudo consultar MongoDB. Comprueba el servidor y los permisos."
            estado = 503
        return render_template("index.html", registros=registros, conectado=conectado,
                               error=error, datos=datos or {"numero": "8", "nombre": "Conexión con MongoDB", "lenguaje": "Python"}), estado

    @app.get("/")
    def inicio():
        return pagina()

    @app.post("/guardar")
    def guardar():
        datos = {campo: request.form.get(campo, "").strip()
                 for campo in ("numero", "nombre", "lenguaje")}
        token = request.form.get("csrf", "")
        if not token or not secrets.compare_digest(token.encode(), session.get("csrf", "").encode()):
            return pagina(datos, "El formulario expiró. Vuelve a enviarlo desde esta página.", 400)
        try:
            numero, documento = validar(datos)
        except ValueError as error:
            return pagina(datos, str(error), 400)

        try:
            resultado = coleccion.update_one({"_id": numero}, {"$set": documento}, upsert=True)
        except ConnectionFailure:
            return pagina(datos, "Se interrumpió la comunicación con MongoDB. Consulta los registros antes de reintentar.", 503)
        except PyMongoError:
            return pagina(datos, "No se pudo completar el guardado. Revisa los permisos de MongoDB.", 503)

        if resultado.upserted_id is not None:
            mensaje = f"Práctica {numero} guardada correctamente."
        elif resultado.modified_count:
            mensaje = f"Práctica {numero} actualizada correctamente."
        else:
            mensaje = f"La práctica {numero} ya contiene esos datos."
        flash(mensaje)
        return redirect(url_for("inicio"), code=303)

    @app.errorhandler(413)
    def formulario_grande(error):
        return pagina(error="El formulario es demasiado grande.", estado=413)

    return app


if __name__ == "__main__":
    print("Abre http://localhost:5000 en tu navegador. Detén la página con Ctrl+C.")
    crear_app().run(host="127.0.0.1", port=5000, debug=False)
FIN_ARCHIVO_PRACTICA08
cat > "$preparada/templates/index.html" <<'FIN_ARCHIVO_PRACTICA08'
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prácticas | Fundamentos de IA</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='estilos.css') }}">
</head>
<body>
  <main>
    <header>
      <div class="marca"><span class="icono">IA</span> FUNDAMENTOS DE IA</div>
      <span class="etiqueta">PRÁCTICA 08</span>
    </header>
    <section class="introduccion">
      <p class="subtitulo">PYTHON + MONGODB</p>
      <h1>Mis prácticas</h1>
      <p>Registra una práctica y consulta la información guardada.</p>
      <span class="estado {{ 'activo' if conectado else 'inactivo' }}">
        {{ 'MongoDB conectado' if conectado else 'MongoDB no disponible' }}
      </span>
    </section>
    {% for mensaje in get_flashed_messages() %}
      <div class="aviso exito" role="status">{{ mensaje }}</div>
    {% endfor %}
    {% if error %}<div class="aviso error" role="alert">{{ error }}</div>{% endif %}
    <div class="paneles">
      <section class="tarjeta">
        <p class="subtitulo">01 / REGISTRO</p>
        <h2>Guardar una práctica</h2>
        <p class="ayuda">Si usas un número existente, actualizarás esa práctica.</p>
        <form action="{{ url_for('guardar') }}" method="post">
          <input type="hidden" name="csrf" value="{{ session['csrf'] }}">
          <label for="numero">Número de práctica</label>
          <input id="numero" name="numero" inputmode="numeric" pattern="[0-9]+"
                 maxlength="19" required value="{{ datos.numero }}">
          <label for="nombre">Nombre</label>
          <input id="nombre" name="nombre" maxlength="120" required value="{{ datos.nombre }}">
          <label for="lenguaje">Lenguaje</label>
          <input id="lenguaje" name="lenguaje" maxlength="40" required value="{{ datos.lenguaje }}">
          <button type="submit">Guardar práctica <span aria-hidden="true">→</span></button>
        </form>
      </section>
      <section class="tarjeta listado">
        <div class="cabecera-listado">
          <div><p class="subtitulo">02 / CONSULTA</p><h2>Prácticas guardadas</h2></div>
          <a class="actualizar" href="{{ url_for('inicio') }}">Actualizar</a>
        </div>
        <p class="ayuda">Hasta 100 registros, ordenados por número.</p>
        {% if registros %}
          <div class="tabla-contenedor">
            <table>
              <caption class="solo-lectores">Prácticas guardadas en MongoDB</caption>
              <thead><tr><th scope="col">N.º</th><th scope="col">Nombre</th><th scope="col">Lenguaje</th></tr></thead>
              <tbody>{% for registro in registros %}
                <tr><td>{{ registro['_id'] }}</td><td>{{ registro.get('nombre', 'Sin nombre') }}</td><td>{{ registro.get('lenguaje', 'Sin especificar') }}</td></tr>
              {% endfor %}</tbody>
            </table>
          </div>
        {% elif conectado %}
          <div class="vacio"><strong>Tu primer registro empieza aquí</strong><p>Completa el formulario y pulsa «Guardar práctica».</p></div>
        {% else %}
          <div class="vacio"><strong>No se pudieron cargar los registros</strong><p>Cuando el servidor esté disponible, pulsa «Actualizar».</p></div>
        {% endif %}
      </section>
    </div>
    <footer>Práctica 08 · Conexión, registro y consulta</footer>
  </main>
</body>
</html>
FIN_ARCHIVO_PRACTICA08
cat > "$preparada/static/estilos.css" <<'FIN_ARCHIVO_PRACTICA08'
:root {
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
  color:#17352e;
  background:#f4f7f4;
  font-synthesis:none;
  line-height:1.5;
}
* {
  box-sizing:border-box;
}
body {
  margin:0;
}
main {
  max-width:1160px;
  padding:28px 30px 20px;
  margin:auto;
}
header {
  display:flex;
  align-items:center;
  justify-content:space-between;
  border-bottom:1px solid #d9e2dc;
  padding-bottom:22px;
  gap:16px;
}
.marca {
  display:flex;
  align-items:center;
  gap:12px;
  font-size:12px;
  font-weight:750;
  letter-spacing:1.6px;
}
.icono {
  background:#174d3d;
  color:#fff;
  border-radius:10px;
  padding:9px;
  letter-spacing:0;
}
.etiqueta {
  font-size:11px;
  letter-spacing:1px;
  border:1px solid #c9d7ce;
  border-radius:30px;
  padding:7px 12px;
}
.introduccion {
  padding:36px 0 28px;
  position:relative;
}
.subtitulo {
  color:#517161;
  font-size:11px;
  font-weight:750;
  letter-spacing:1.8px;
  margin:0 0 8px;
}
h1 {
  font-size:44px;
  letter-spacing:-1.8px;
  margin:0 0 6px;
  line-height:1.2;
}
h2 {
  font-size:21px;
  letter-spacing:-.5px;
  margin:0 0 10px;
}
.introduccion>p:not(.subtitulo) {
  color:#576c60;
  margin:0;
}
.estado {
  display:inline-flex;
  gap:8px;
  align-items:center;
  border-radius:30px;
  padding:7px 13px;
  font-size:12px;
  font-weight:650;
  margin-top:18px;
}
.estado:before {
  content:"";
  width:7px;
  height:7px;
  border-radius:50%;
  background:currentColor;
}
.activo {
  background:#e1efdf;
  color:#245b34;
}
.inactivo {
  background:#f8e6df;
  color:#8b392c;
}
.paneles {
  display:grid;
  grid-template-columns:minmax(260px,.85fr) minmax(0,1.35fr);
  gap:24px;
  align-items:start;
}
.tarjeta {
  background:#fff;
  border:1px solid #dbe4dd;
  border-radius:17px;
  padding:28px;
  box-shadow:0 4px 15px #183a2510;
}
.ayuda {
  font-size:13px;
  color:#647568;
  margin:0 0 24px;
}
label {
  display:block;
  font-size:13px;
  font-weight:650;
  margin:18px 0 7px;
}
input {
  display:block;
  width:100%;
  font:inherit;
  font-size:14px;
  color:#18392d;
  border:1px solid #bdcdc1;
  border-radius:8px;
  background:#fbfcfa;
  padding:11px 12px;
}
input:focus-visible,button:focus-visible,a:focus-visible {
  outline:3px solid #8eae38;
  outline-offset:3px;
}
button {
  margin-top:25px;
  width:100%;
  border:0;
  background:#184f3d;
  color:#fff;
  border-radius:9px;
  padding:13px 16px;
  font:inherit;
  font-weight:650;
  cursor:pointer;
  display:flex;
  justify-content:space-between;
  align-items:center;
}
button:hover {
  background:#0d3d2d;
}
.cabecera-listado {
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:12px;
}
.actualizar {
  color:#245943;
  font-size:12px;
  font-weight:650;
  text-decoration:underline;
  text-underline-offset:4px;
}
.tabla-contenedor {
  overflow-x:auto;
}
table {
  width:100%;
  border-collapse:collapse;
  text-align:left;
  font-size:13px;
}
th {
  background:#f0f5ef;
  color:#506a57;
  font-size:11px;
  letter-spacing:.5px;
  padding:12px;
}
td {
  padding:16px 12px;
  border-bottom:1px solid #e7ede7;
  overflow-wrap:anywhere;
}
td:first-child {
  font-weight:750;
}
td:last-child {
  color:#58725e;
}
.vacio {
  border:1px dashed #b7cbbd;
  background:#f8faf6;
  border-radius:12px;
  text-align:center;
  padding:48px 22px;
  margin-top:8px;
}
.vacio strong {
  font-size:15px;
}
.vacio p {
  font-size:13px;
  color:#657467;
  margin:8px 0 0;
}
.aviso {
  padding:14px 18px;
  border-radius:10px;
  font-size:14px;
  margin:0 0 20px;
}
.exito {
  background:#e2efd9;
  border:1px solid #baceac;
  color:#31532a;
}
.error {
  background:#fbeae4;
  border:1px solid #e2b6a7;
  color:#852c1e;
}
footer {
  text-align:center;
  font-size:11px;
  color:#69806d;
  padding:28px 0 0;
}
.solo-lectores {
  position:absolute;
  width:1px;
  height:1px;
  overflow:hidden;
  clip-path:inset(50%);
}
@media(max-width:760px) {
  main {
    padding:20px 16px;
  }
  .paneles {
    grid-template-columns:1fr;
  }
  .tarjeta {
    padding:22px;
  }
  h1 {
    font-size:36px;
  }
  .introduccion {
    padding:28px 0;
  }
  .marca {
    font-size:10px;
    letter-spacing:.8px;
  }
  .etiqueta {
    font-size:9px;
  }
  .cabecera-listado {
    flex-wrap:wrap;
  }
}
FIN_ARCHIVO_PRACTICA08
cat > "$preparada/requirements.txt" <<'FIN_ARCHIVO_PRACTICA08'
Flask>=3.1,<4
pymongo>=4.6,<5
FIN_ARCHIVO_PRACTICA08
cat > "$preparada/ejecutar.sh" <<'FIN_ARCHIVO_PRACTICA08'
#!/usr/bin/env bash
set -euo pipefail
directorio="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
proyecto="$(cd -- "$directorio/../../.." && pwd)"
exec "$proyecto/.venv/bin/python" "$directorio/08_conexion_mongodb.py"
FIN_ARCHIVO_PRACTICA08
cat > "$preparada/README.md" <<'FIN_ARCHIVO_PRACTICA08'
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
FIN_ARCHIVO_PRACTICA08

if [[ ! -x "$proyecto/.venv/bin/python" ]]; then
  python3 -m venv "$proyecto/.venv"
fi
"$proyecto/.venv/bin/python" -m pip install -r "$preparada/requirements.txt"
"$proyecto/.venv/bin/python" -c 'import ast, sys; from pathlib import Path; ast.parse(Path(sys.argv[1]).read_text()); import flask, pymongo; print("Flask y PyMongo disponibles en el entorno del proyecto.")' "$preparada/08_conexion_mongodb.py"
if [[ -e "$destino" ]]; then
  carpeta_respaldos="$(dirname -- "$proyecto")/$(basename -- "$proyecto")-respaldos"
  mkdir -p -- "$carpeta_respaldos"
  respaldo="$(mktemp -d "$carpeta_respaldos/practica-08-XXXXXX")"
  mv -- "$destino" "$respaldo/practica-08-conexion-mongodb"
  anterior_movida=1
fi
mv -- "$preparada" "$destino"
instalada=1
echo "Práctica 8 instalada en: $destino"
if [[ -n "$respaldo" ]]; then echo "Versión anterior guardada en: $respaldo"; fi
echo "Desde la raíz del proyecto ejecuta:"
echo "bash unidad-01-introduccion-ia/practicas/practica-08-conexion-mongodb/ejecutar.sh"
echo "Después abre http://localhost:5000 en tu navegador."
