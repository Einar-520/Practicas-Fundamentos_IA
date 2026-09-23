# Práctica 10: agente de climatización con consultas, gráficas y CRUD

Aplicación independiente de Python con **Streamlit** y MongoDB Atlas. Conserva
el agente reactivo simple y las reglas del profesor. La interfaz vigente se abre
en el navegador y permite decidir qué información consultar:

1. **Arriba:** selecciona una acción del agente o Todas las acciones.
2. **En medio:** consulta los registros que cumplen la selección.
3. **Abajo:** observa las gráficas de temperatura y humedad de esos registros.

El panel lateral permite crear, editar y eliminar lecturas. La interfaz anterior
con Tkinter queda en el historial de Git; esta carpeta contiene la versión actual.

## Ejecutar en VS Code con WSL

Desde la terminal WSL, guarda los archivos abiertos y ejecuta:

```bash
cd ~/universidad/fundamentos-ia &&
git pull --ff-only origin main &&
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/requirements.txt &&
bash unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/ejecutar.sh
```

Si aún no tienes el entorno virtual, créalo antes de instalar dependencias con
`python3 -m venv .venv` desde la raíz del proyecto. Selecciona `.venv/bin/python`
como intérprete de VS Code.

Abre **http://localhost:8510** en el navegador. Mantén abierta la terminal;
**Ctrl+C** detiene la aplicación. No necesita WSLg ni instalar Tkinter.
El lanzador prepara el `.env`, conserva su contenido si ya existe y abre
Streamlit escuchando únicamente en `127.0.0.1`.

Para volver a abrir la práctica después de instalar las dependencias:

```bash
bash unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/ejecutar.sh
```

También se puede iniciar directamente, una vez preparado el `.env`:

```bash
.venv/bin/python -m streamlit run unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/10_agente_climatizacion.py --server.address 127.0.0.1 --server.port 8510
```

## Reglas conservadas

| Condición | Acción |
| --- | --- |
| Temperatura > 30 °C y humedad > 70 % | Encender aire acondicionado (Modo Deshumidificador) |
| Temperatura > 30 °C y humedad ≤ 70 % | Encender ventilador |
| Temperatura < 18 °C | Encender calefacción |
| Temperatura entre 18 y 30 °C, incluidos ambos límites | Mantener sistema apagado |

Se mantiene el orden original de evaluación. A 18 o 30 °C, el sistema permanece
apagado; con temperatura mayor de 30 °C y humedad exactamente de 70 %, se elige
el ventilador. La humedad debe estar entre 0 y 100 %. Los campos aceptan punto o
coma decimal y rechazan entradas vacías, texto, infinito y NaN.

## Consultar una acción y ver sus gráficas

Por ejemplo, selecciona **Encender ventilador** en el selector superior. MongoDB
consulta tus registros cuya acción guardada coincide exactamente con esa opción.
El filtro se aplica antes de paginar, por lo que también encuentra coincidencias
que no estaban en la primera página de Todas las acciones.

La tabla muestra hasta 50 registros por página, del más reciente al más antiguo.
Usa **Anterior** y **Siguiente** para recorrerlos. Al cambiar de acción se vuelve
a la primera página y se descarta cualquier selección de edición o eliminación.
**Actualizar registros** repite la consulta de la página actual.

Las dos gráficas y sus promedios usan los registros de la página visible, no el
historial completo de la colección. Cambian junto con el filtro y la página.
Las líneas se ordenan cronológicamente y muestran puntos incluso cuando solo hay
una lectura. Las fechas, los ejes y el detalle al pasar el cursor se muestran en
UTC. La tabla conserva el orden de consulta; ordenar una columna en el navegador
no cambia los registros usados por las gráficas.

Si no hay coincidencias, se informa sin inventar datos. Si hay registros antiguos
con fechas o valores inválidos, permanecen en la tabla y se indica cuántos no se
pueden graficar. Un error de consulta retira la tabla y las gráficas anteriores
para evitar que parezcan corresponder a una selección nueva.

## CRUD en el panel lateral

| Operación | Pasos |
| --- | --- |
| Crear | Elige Crear, escribe temperatura y humedad y pulsa Crear registro. El agente decide la acción y la guarda en Atlas. |
| Consultar | Utiliza el selector de acción, la tabla y los botones de página del panel principal. |
| Editar | Elige Editar, selecciona un registro de la página visible, cambia sus valores y pulsa Guardar cambios. El agente recalcula la acción. |
| Eliminar | Elige Eliminar, selecciona un registro, verifica su ID y lectura, marca la confirmación y pulsa Eliminar registro. |

Al editar se conserva el `_id` y la fecha de creación, y se actualiza
`actualizado_en`. Si la acción recalculada ya no coincide con el filtro activo,
el registro sale de esa consulta; el mensaje indica qué acción seleccionar para
verlo. Lo mismo se aplica al crear una lectura con una acción diferente del filtro.

Solo se escribe al enviar un formulario. Cambiar de acción, de página o refrescar
la consulta no inserta lecturas. Streamlit vuelve a ejecutar la interfaz al
interactuar; los formularios y el estado de la sesión separan esas consultas de
los envíos del CRUD. Cada operación cierra su cliente de MongoDB al finalizar.

Una escritura confirmada se informa por separado de la consulta posterior.
Si falla ese refresco, el guardado sigue confirmado. Cuando no se puede confirmar
una escritura, el programa pide actualizar los registros antes de reenviar:
pudo haberse aplicado. Los errores de consulta bloquean nuevas escrituras hasta
que se complete una consulta correcta.

## Configuración del clúster del profesor

El `.env` pertenece únicamente a la práctica 10 y se lee junto a
`configuracion.py`, independientemente de la carpeta de ejecución:

```dotenv
Mongo_User='hector1985'
Mongo_Password=''
Mongo_Closter='utvt.qqqotrr.mongodb.net'
Mongo_DB='Einar_Ivan_Lazcano_Luna'
Mongo_Collection='climatizacion'
```

La contraseña real va solo en tu archivo local. Se conserva el nombre de variable
`Mongo_Closter` del enunciado. El nombre de la base utiliza guiones bajos porque
MongoDB no admite espacios en nombres de bases de datos.

`preparar_env.py` conserva y valida un `.env` existente. Si falta, reutiliza
localmente usuario, contraseña y clúster de la práctica 9 cuando están disponibles,
y crea la configuración propia de la 10 para tu base y la colección
`climatizacion`. Si no existe ese acceso local, pide la contraseña oculta en la
terminal. No cambia el archivo de la práctica 9.

`configuracion.py` construye `mongo_url` con `mongodb+srv`, codifica las credenciales
y utiliza `retryWrites=true`, `w=majority` y `authSource=admin`. La URL completa
no se muestra en pantalla. El profesor debe autorizar tu IP y conceder permisos
de lectura y escritura sobre tu base en Atlas.

Las consultas usan `{ practica: 10, alumno: "Einar Ivan Lazcano Luna" }` y agregan
`accion` si seleccionas una. Las actualizaciones y eliminaciones añaden el `_id`
al filtro por alumno y práctica. Son límites de esta aplicación; los permisos
reales son los que el profesor haya asignado al usuario de Atlas.

## Documento guardado

```javascript
{
  _id: ObjectId("..."),
  practica: 10,
  alumno: "Einar Ivan Lazcano Luna",
  agente: "AgenteClimatizacion",
  temperatura: 32.5,
  humedad: 60.0,
  accion: "Encender ventilador",
  fecha: ISODate("...")
}
```

La primera inserción crea la colección si no existe. La edición agrega
`actualizado_en` sin alterar `fecha`; ambas se guardan como fechas BSON en UTC.
El agente registra su decisión: no controla físicamente dispositivos.

## Archivos y conceptos

| Archivo | Responsabilidad |
| --- | --- |
| `10_agente_climatizacion.py` | Punto de entrada de Streamlit. |
| `agente_climatizacion.py` | Percepción, validación, reglas y ejecución del agente. Comparte las cuatro acciones con el filtro. |
| `almacenamiento_atlas.py` | CRUD y consulta por acción antes de paginar. |
| `interfaz.py` | Selector, tabla, formularios del CRUD y gráficas. |
| `configuracion.py` | Lee el `.env` y construye `mongo_url`. |
| `preparar_env.py` | Prepara la configuración local sin sobrescribirla. |
| `ejecutar.sh` | Inicia Streamlit con el intérprete del proyecto. |
| `requirements.txt` | PyMongo, python-dotenv, Streamlit, pandas y Altair. |
| `tests/` | Reglas, filtros, CRUD, configuración y flujos de Streamlit con Atlas simulado. |

**pandas** organiza los datos de la consulta en una tabla y normaliza fechas y
números. **Altair**, integrado mediante `st.altair_chart`, describe las gráficas
con ejes, unidades, puntos y detalle al pasar el cursor. La tabla y las gráficas
comparten los mismos datos consultados; no hay una segunda consulta que pueda
mezclar otra acción o página.

## Verificación

```bash
.venv/bin/python -m unittest discover -s unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/tests -v
```

Pasaron 34 pruebas, incluidas las 50 combinaciones de las reglas originales.
Se verificaron las cuatro acciones, paginación filtrada, registros de otros
alumnos, entradas inválidas, CRUD completo, confirmación de eliminación, cambio
de acción al editar, resultados vacíos y fallos de conexión. Las pruebas de
Streamlit comprueban también que los IDs y valores enviados a ambas gráficas
coinciden con los de la tabla y que consultar no duplica inserciones.

Las pruebas usan una colección simulada y no modifican datos del profesor.
El servidor Streamlit arrancó y respondió correctamente al control HTTP de salud.
La revisión visual en navegador queda pendiente; los controles y los datos de
las gráficas sí se verificaron mediante AppTest.
La conexión real depende del `.env`, los permisos y la IP autorizada de tu laptop.
Para comprobarla, crea una lectura de 32 °C y 60 %, selecciona Encender ventilador
y verifica que aparece en la tabla y en las dos gráficas. Al editarla a 25 °C,
debe pasar a Mantener sistema apagado conservando su ID.

## Referencias

- [Formularios de Streamlit](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form).
- [Gráficas de Altair en Streamlit](https://docs.streamlit.io/develop/api-reference/charts/st.altair_chart).
- [Pruebas de aplicaciones Streamlit](https://docs.streamlit.io/develop/api-reference/app-testing).
- [Actualizaciones con PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/update/).
