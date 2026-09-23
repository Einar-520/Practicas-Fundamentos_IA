# Práctica 10: CRUD del agente de climatización con Tkinter y MongoDB Atlas

Programa independiente que implementa el agente reactivo simple del profesor.
La ventana captura temperatura y humedad, el agente decide qué acción corresponde
y el propio agente registra la percepción y la acción en el clúster del profesor.
La interfaz permite crear, consultar, actualizar y eliminar esos registros.

## Reglas originales

Se conserva el orden de evaluación y las comparaciones estrictas del enunciado:

| Condición | Acción |
| --- | --- |
| Temperatura > 30 °C y humedad > 70 % | Encender aire acondicionado (Modo Deshumidificador) |
| Temperatura > 30 °C y humedad ≤ 70 % | Encender ventilador |
| Temperatura < 18 °C | Encender calefacción |
| Temperatura entre 18 y 30 °C, incluidos ambos límites | Mantener sistema apagado |

A 30 °C se mantiene apagado aunque la humedad sea alta. A 18 °C también permanece
apagado. Con temperatura mayor de 30 °C y humedad exactamente de 70 %, se enciende
el ventilador. La humedad debe estar entre 0 y 100 %. Se aceptan punto y coma
decimal, y se rechazan campos vacíos, texto, infinito y NaN.

## Ejecutar desde VS Code con WSL

Guarda los archivos abiertos y ejecuta desde la raíz del proyecto:

```bash
cd ~/universidad/fundamentos-ia &&
git pull --ff-only origin main &&
sudo apt update &&
sudo apt install -y python3-tk &&
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/requirements.txt &&
bash unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/ejecutar.sh
```

Si todavía no tienes el entorno del proyecto, créalo con python3 -m venv .venv
antes de instalar las dependencias. Selecciona .venv/bin/python como intérprete
en VS Code. Se abre una ventana Tkinter. Para probar el soporte gráfico ejecuta
.venv/bin/python -m tkinter; WSL necesita soporte WSLg. Tkinter se instala mediante
el paquete del sistema correspondiente al intérprete, no con pip.

También puedes ejecutar 10_agente_climatizacion.py desde VS Code una vez que hayas
preparado el entorno y el .env. El archivo ejecutar.sh hace las comprobaciones y
prepara la configuración antes de abrir la ventana.

## Configuración del clúster del profesor

El archivo .env pertenece únicamente a la práctica 10. Se lee junto a
configuracion.py independientemente de la carpeta desde la que ejecutes Python.

```dotenv
Mongo_User='hector1985'
Mongo_Password=''
Mongo_Closter='utvt.qqqotrr.mongodb.net'
Mongo_DB='Einar_Ivan_Lazcano_Luna'
Mongo_Collection='climatizacion'
```

La contraseña real se conserva exclusivamente en tu .env local. Se mantiene
Mongo_Closter con la escritura del enunciado. Los guiones bajos en Mongo_DB
permiten utilizar tu nombre sin espacios en el nombre de la base.

Al ejecutar preparar_env.py o ejecutar.sh:

1. Si el .env de la práctica 10 ya existe, se valida y se conserva.
2. Si no existe y tienes el .env de la práctica 9, se reutilizan localmente su
   usuario, contraseña y clúster, conservando intacto el archivo de la 9.
3. Se crea un .env propio para Einar_Ivan_Lazcano_Luna y la colección climatizacion.
4. Si tampoco existe la configuración de la 9, se solicita la contraseña en la
   terminal de forma oculta. El archivo nuevo se crea con permisos 600.

Después de crear su configuración, la práctica 10 funciona sin importar módulos
ni leer archivos de otras prácticas. No se publica ninguna contraseña ni el
archivo .env; .env.example es la plantilla sin contraseña.

configuracion.py construye mongo_url con el protocolo mongodb+srv, codifica las
credenciales con quote_plus y configura retryWrites=true, w=majority y
authSource=admin. PyMongo usa esa variable para crear el cliente; el enlace
completo nunca se muestra en la ventana ni se imprime en la terminal.

El profesor debe tener autorizada tu IP pública en Atlas y conceder al usuario
permisos de consulta, inserción, actualización y eliminación sobre tu base.
El programa utiliza la base y
colección indicadas en el .env; no modifica usuarios ni permisos del clúster.

## Funcionamiento de la ventana

| Operación | Cómo usarla | Operación en Atlas |
| --- | --- | --- |
| Crear | Escribe temperatura y humedad y pulsa **Crear registro**. | El agente calcula la acción e inserta un documento con `insert_one`. |
| Consultar | Pulsa **Actualizar lista** y selecciona una fila para ver su detalle. Usa **Anterior** y **Siguiente** para recorrer páginas de 50 registros. | `find` obtiene tus registros de la práctica 10, ordenados del más reciente al más antiguo. |
| Actualizar | Selecciona una fila, cambia temperatura o humedad y pulsa **Guardar cambios**. | El agente recalcula la acción y `update_one` modifica ese mismo documento. |
| Eliminar | Selecciona una fila y pulsa **Eliminar seleccionado**. Confirma en el cuadro que muestra el identificador y la lectura. | `delete_one` elimina únicamente el documento seleccionado. |

**Nuevo / limpiar** vacía el formulario y deja de editar la fila seleccionada.
Úsalo antes de crear otro registro. **Ctrl + Enter** crea un registro en modo nuevo
o guarda los cambios del seleccionado en modo edición. La pestaña **Detalle del
seleccionado** muestra el documento completo, incluido su `_id`.

Al abrir la ventana se consulta la lista; no se generan ni se insertan lecturas
automáticas. Después de una consulta correcta se habilitan las operaciones.
Cada creación válida genera un documento nuevo; MongoDB asigna su `_id` y crea
la colección con la primera inserción si todavía no existe.

Las consultas, actualizaciones y eliminaciones se limitan a
`{ practica: 10, alumno: "Einar Ivan Lazcano Luna" }`. Para modificar o eliminar
se añade el `_id` seleccionado al filtro. La edición no crea documentos cuando
el seleccionado ya no existe. Este filtro delimita los registros de la práctica;
los permisos efectivos siguen siendo los del usuario configurado en Atlas.

La ventana muestra la decisión calculada aunque la conexión falle y distingue
el cálculo de una escritura confirmada por Atlas. Si la escritura se confirma
pero falla la consulta posterior, informa que el cambio se guardó y solicita
**Actualizar lista**. Si la escritura no pudo confirmarse, revisa la lista antes
de reenviar porque pudo haberse aplicado. La interfaz no reenvía escrituras
automáticamente; después de un error bloquea cambios hasta refrescar la lista.

Durante las operaciones de red, los botones y campos se deshabilitan para evitar
envíos simultáneos. El hilo de trabajo no accede a widgets: los resultados vuelven
mediante una cola y after. Si cierras la ventana con una operación pendiente,
espera a que termine y cierra el cliente MongoDB.

## Documento insertado

Ejemplo de una lectura de 35 °C y 80 % de humedad:

```javascript
{
  _id: ObjectId("..."),
  practica: 10,
  alumno: "Einar Ivan Lazcano Luna",
  agente: "AgenteClimatizacion",
  temperatura: 35.0,
  humedad: 80.0,
  accion: "Encender aire acondicionado (Modo Deshumidificador)",
  fecha: ISODate("...")
}
```

La fecha de creación se guarda en UTC como fecha BSON. Al editar se conserva
`fecha` y se añade o renueva `actualizado_en`, también en UTC. La acción siempre
se recalcula a partir de la temperatura y la humedad actualizadas.

La ventana muestra las fechas en representación ISO y el identificador devuelto
por MongoDB. Para comprobarlo en Atlas o Compass,
abre la base Einar_Ivan_Lazcano_Luna, colección climatizacion, y filtra por
`{ practica: 10, alumno: "Einar Ivan Lazcano Luna" }`.

## Estructura y conceptos para explicar al profesor

| Archivo | Responsabilidad |
| --- | --- |
| 10_agente_climatizacion.py | Punto de entrada del programa. |
| agente_climatizacion.py | Clase AgenteClimatizacion, validación y reglas originales. |
| interfaz.py | Ventana Tkinter, controles y trabajo en segundo plano. |
| almacenamiento_atlas.py | Conexión y CRUD: insert_one, find, update_one y delete_one. |
| configuracion.py | Lee el .env y construye mongo_url. |
| preparar_env.py | Prepara el .env local sin exponer credenciales. |
| ejecutar.sh | Inicia la práctica usando el entorno .venv del proyecto. |
| requirements.txt | PyMongo y python-dotenv. |
| tests/test_practica10.py | Pruebas con Atlas simulado y prueba gráfica opcional. |

El agente es **reactivo simple** porque decide únicamente con la percepción actual.
El registro histórico no modifica las reglas del profesor. La separación es:

1. percibir(): recibe los valores de la interfaz y valida las dos entradas.
2. tomar_decision(): aplica las reglas condición-acción en el orden original.
3. mostrar_resultado(): entrega el resumen para mostrarlo en la ventana.
4. ejecutar(): el propio agente construye el documento con sus datos y llama al
   almacenamiento para insertarlo o actualizar el registro seleccionado en Atlas.

La ejecución de esta práctica consiste en registrar la acción elegida en Atlas.
La clase recibe el almacenamiento como argumento para poder probar el mismo
agente con una colección simulada, sin cambiar su lógica ni usar credenciales reales.

## Verificación

```bash
.venv/bin/python -m unittest discover -s unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/tests -v
```

Pasaron 29 pruebas y se omitió una prueba de widgets reales por falta de pantalla
gráfica. Se verificaron 50 combinaciones de temperatura y humedad contra las
reglas originales, entradas inválidas, el flujo completo del CRUD, paginación,
conservación de la fecha de creación, filtros por alumno y práctica, cancelación
de la eliminación, errores de conexión y escrituras confirmadas cuyo refresco
posterior falla. También se comprobó que una operación pendiente impide envíos
simultáneos y que el cierre espera antes de desconectar el cliente.

Estas pruebas usan una colección simulada y no alteran datos del profesor.
La apertura visual y la conexión real se comprueban en tu laptop con WSLg y tu
`.env`. Para verificar el CRUD, crea una lectura de 35 °C y 80 %: debe guardarse
la acción de aire acondicionado. Selecciónala, cambia a 25 °C y guarda: debe
conservar su `_id` y cambiar la acción a mantener el sistema apagado. Consulta
el resultado y, si ya no necesitas ese registro de prueba, elimínalo desde la
interfaz y comprueba que desaparece de la lista y de Atlas.

## Referencias

- [Tkinter y su modelo de eventos](https://docs.python.org/3/library/tkinter.html).
- [Inserción de documentos con PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/insert/).
- [Actualización de documentos con PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/update/).
- [Eliminación de documentos con PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/delete/).
- [Aplicaciones gráficas en WSL](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps).
