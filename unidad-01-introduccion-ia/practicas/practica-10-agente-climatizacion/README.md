# Práctica 10: agente de climatización con Tkinter y Matplotlib

Programa independiente de escritorio con consultas por acción, gráficas y CRUD
en el clúster de MongoDB Atlas del profesor. La versión vigente usa **Tkinter**
para la ventana y **Matplotlib** para las gráficas integradas en ella.

La ventana mantiene esta distribución:

1. **Arriba:** selector de acción y regla correspondiente.
2. **En medio:** tabla de registros que coinciden con la acción seleccionada.
3. **Abajo:** gráficas de temperatura y humedad de esos registros.

El panel lateral permite crear, editar, eliminar y consultar el detalle del
registro seleccionado. Las versiones anteriores están en el historial de Git.

## Ejecutar en VS Code con WSL

Desde la raíz del proyecto, con los archivos del editor guardados:

```bash
cd ~/universidad/fundamentos-ia &&
git pull --ff-only origin main &&
sudo apt install -y python3-tk &&
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/requirements.txt &&
bash unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/ejecutar.sh
```

Si todavía no existe el entorno del proyecto, créalo con `python3 -m venv .venv`
antes de instalar las dependencias. Selecciona `.venv/bin/python` como intérprete
en VS Code. Tkinter se instala con el paquete del sistema correspondiente a ese
intérprete; Matplotlib y las dependencias de Atlas se instalan con pip.

Se abre una ventana de escritorio. WSL necesita soporte gráfico WSLg. Comprueba
Tkinter con `.venv/bin/python -m tkinter`. La aplicación no utiliza un servidor
localhost. Una vez preparado el entorno, basta ejecutar:

```bash
bash unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/ejecutar.sh
```

También puedes ejecutar `10_agente_climatizacion.py` desde VS Code cuando el
entorno y el `.env` ya estén preparados.

## Reglas originales

| Condición | Acción |
| --- | --- |
| Temperatura > 30 °C y humedad > 70 % | Encender aire acondicionado (Modo Deshumidificador) |
| Temperatura > 30 °C y humedad ≤ 70 % | Encender ventilador |
| Temperatura < 18 °C | Encender calefacción |
| Temperatura entre 18 y 30 °C, incluidos ambos límites | Mantener sistema apagado |

Se mantiene el orden del profesor. A 18 o 30 °C, el sistema queda apagado. Con
más de 30 °C y humedad exactamente de 70 %, se elige el ventilador. Los campos
aceptan punto o coma decimal y rechazan entradas vacías, texto, infinito y NaN.
La humedad debe estar entre 0 y 100 %.

## Consultas y gráficas

Selecciona **Encender ventilador**, por ejemplo: la consulta a MongoDB filtra esa
acción antes de paginar y muestra solo tus registros correspondientes. También
puedes elegir **Todas las acciones**.

Cada página contiene hasta 50 registros, ordenados del más reciente al más
antiguo. Usa **Anterior**, **Siguiente** y **Actualizar lista** para recorrerlos
o volver a consultar. Cambiar de acción reinicia la página y limpia la selección
anterior. Seleccionar una fila carga sus datos en el panel lateral.

Las gráficas y sus promedios usan los registros de la página visible, no todo el
historial. Sus fechas se ordenan cronológicamente en UTC. Los puntos permiten
representar una sola lectura. Los registros con fechas o valores inválidos se
conservan en la tabla y se informa cuántos no pueden graficarse.

El selector cambia la consulta sin insertar datos. Si no hay coincidencias se
muestra un estado vacío. Si falla una consulta, se retiran los resultados y las
gráficas anteriores para que no parezcan datos actuales.

## CRUD

| Operación | Uso |
| --- | --- |
| Crear | Escribe temperatura y humedad y pulsa Crear registro. El agente decide y guarda la acción en Atlas. |
| Consultar | Selecciona una acción y recorre la tabla; la fila seleccionada muestra su documento completo al lado. |
| Actualizar | Selecciona una fila, modifica temperatura o humedad y pulsa Guardar cambios. El agente recalcula la acción. |
| Eliminar | Selecciona una fila, pulsa Eliminar seleccionado y confirma su ID y lectura en el diálogo. |

**Nuevo / limpiar** vacía el formulario para crear otra lectura. **Ctrl + Enter**
crea un registro o guarda los cambios del seleccionado, según el modo actual.
Al editar se conserva el `_id` y la fecha de creación y se actualiza
`actualizado_en`. Si la acción recalculada sale del filtro activo, el mensaje
indica qué acción consultar para volver a encontrar el registro.

Las operaciones de Atlas se realizan en un hilo de trabajo y los resultados
vuelven mediante una cola y `after`; los widgets y Matplotlib se actualizan en
el hilo principal. Durante una operación se deshabilitan los controles. Al
cerrar se espera la operación pendiente y se libera el cliente de MongoDB.

Una escritura confirmada se informa por separado de una consulta posterior
fallida. Si no pudo confirmarse una escritura, actualiza la lista antes de
reenviar: pudo haberse aplicado. El programa bloquea nuevas escrituras hasta
que se complete una consulta correcta.

## Configuración de Atlas

La práctica conserva su propio `.env`, junto a `configuracion.py`:

```dotenv
Mongo_User='hector1985'
Mongo_Password=''
Mongo_Closter='utvt.qqqotrr.mongodb.net'
Mongo_DB='Einar_Ivan_Lazcano_Luna'
Mongo_Collection='climatizacion'
```

La contraseña real permanece solo en tu archivo local. `Mongo_Closter` conserva
la escritura del enunciado; la base usa guiones bajos porque MongoDB no admite
espacios en ese nombre. El `.env` existente se valida y conserva. Si falta,
`preparar_env.py` reutiliza localmente el acceso de la práctica 9 si existe,
y crea una configuración propia para tu base y la colección `climatizacion`.
Si tampoco existe ese acceso, solicita la contraseña oculta en la terminal.

`configuracion.py` construye `mongo_url` con `mongodb+srv`, credenciales codificadas,
`retryWrites=true`, `w=majority` y `authSource=admin`. No muestra la URL completa.
El profesor debe autorizar tu IP y conceder permisos de lectura y escritura.

Las consultas se limitan a `{ practica: 10, alumno: "Einar Ivan Lazcano Luna" }`
y agregan `accion` cuando corresponde. La edición y eliminación añaden el `_id`
seleccionado. Los permisos efectivos siguen siendo los del usuario de Atlas.

Cada documento contiene `_id`, `practica`, `alumno`, `agente`, `temperatura`,
`humedad`, `accion` y `fecha`. Una edición agrega `actualizado_en`. Ambas fechas
se guardan en UTC como fechas BSON. El agente registra la decisión y no controla
físicamente dispositivos.

## Archivos

| Archivo | Responsabilidad |
| --- | --- |
| `10_agente_climatizacion.py` | Punto de entrada de la ventana. |
| `agente_climatizacion.py` | Percepción, validación, reglas y ejecución del agente. |
| `almacenamiento_atlas.py` | CRUD y consulta filtrada antes de paginar. |
| `interfaz.py` | Ventana Tkinter, selector, tabla, formularios y ejecución en segundo plano. |
| `graficas.py` | Preparación de series y dibujo con Matplotlib. |
| `configuracion.py` | Lectura del `.env` y construcción de `mongo_url`. |
| `preparar_env.py` | Preparación de la configuración local. |
| `ejecutar.sh` | Inicio con el intérprete del proyecto. |
| `requirements.txt` | PyMongo, python-dotenv y Matplotlib. |
| `tests/` | Reglas, filtros, CRUD, configuración, controles y gráficas. |

`FigureCanvasTkAgg` integra la figura de Matplotlib en un marco de Tkinter.
Se reutilizan las mismas reglas y la misma consulta para la tabla y las gráficas.

## Verificación

```bash
.venv/bin/python -m unittest discover -s unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/tests -v
```

Pasaron 38 pruebas y se omitió una prueba de ventana real por falta de pantalla.
Se verificaron las 50 combinaciones de las reglas originales, el filtro de las
cuatro acciones, paginación, entradas inválidas, CRUD, cancelación de eliminación,
cierre con trabajo pendiente, errores de conexión y correspondencia entre tabla
y gráficas. Matplotlib dibujó las figuras con su motor sin pantalla.

Estas pruebas usan una colección simulada. La ventana en WSLg y la conexión real
al clúster se comprueban en tu laptop con su `.env`. Crea una lectura de 32 °C y
60 %, selecciona Encender ventilador y verifica la fila y los puntos de ambas
gráficas. Al editarla a 25 °C, debe pasar a Mantener sistema apagado con el mismo ID.

## Referencias

- [Integrar Matplotlib en Tkinter](https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_tk_sgskip.html).
- [Tkinter y su modelo de eventos](https://docs.python.org/3/library/tkinter.html).
