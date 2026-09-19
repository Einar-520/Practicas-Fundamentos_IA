# Práctica 10: agente de climatización con Tkinter y MongoDB Atlas

Programa independiente que implementa el agente reactivo simple del profesor.
La ventana captura temperatura y humedad, el agente decide qué acción corresponde
y el propio agente registra la percepción y la acción en el clúster de Atlas.

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
permisos de escritura y consulta sobre tu base. El programa utiliza la base y
colección indicadas en el .env; no modifica usuarios ni permisos del clúster.

## Funcionamiento de la ventana

- **Evaluar y guardar:** valida las entradas, muestra la decisión y envía un
  registro nuevo a Atlas. También puedes usar Ctrl + Enter.
- **Consultar último registro:** lee el registro más reciente de la práctica 10
  en la colección configurada, sin insertar datos.
- **Limpiar:** vacía temperatura y humedad; los registros de Atlas se conservan.

Abrir la ventana no inserta datos. Cada pulsación válida de Evaluar y guardar
crea un documento nuevo. La inserción utiliza insert_one; MongoDB asigna un _id.
La colección se crea con la primera inserción si todavía no existe.

La ventana muestra la decisión calculada aunque la conexión falle y distingue
el cálculo de un guardado confirmado por Atlas. No se realizan reintentos
automáticos desde la interfaz. Si la conexión se interrumpe y no se confirma el
guardado, consulta el último registro antes de reenviar; pudo haberse insertado.
La última consulta visible se marca como posiblemente antigua tras un error.

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

La fecha se guarda en UTC como fecha BSON. La ventana muestra su representación
ISO y el identificador devuelto por MongoDB. Para comprobarlo en Atlas o Compass,
abre la base Einar_Ivan_Lazcano_Luna, colección climatizacion, y filtra por
`{ practica: 10 }`. Las inserciones nuevas conservan los registros anteriores.

## Estructura y conceptos para explicar al profesor

| Archivo | Responsabilidad |
| --- | --- |
| 10_agente_climatizacion.py | Punto de entrada del programa. |
| agente_climatizacion.py | Clase AgenteClimatizacion, validación y reglas originales. |
| interfaz.py | Ventana Tkinter, controles y trabajo en segundo plano. |
| almacenamiento_atlas.py | Conexión, insert_one, consulta y cierre del cliente. |
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
4. ejecutar(): el propio agente crea el documento con sus datos y llama al
   almacenamiento para insertarlo en Atlas.

La ejecución de esta práctica consiste en registrar la acción elegida en Atlas.
La clase recibe el almacenamiento como argumento para poder probar el mismo
agente con una colección simulada, sin cambiar su lógica ni usar credenciales reales.

## Verificación

```bash
.venv/bin/python -m unittest discover -s unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/tests -v
```

Pasaron 17 pruebas, incluyendo 50 combinaciones de temperatura y humedad comparadas
con las reglas originales, validación, inserciones nuevas, consulta, errores,
configuración privada, cierre de conexión y operaciones de fondo sin envíos
simultáneos. La prueba de widgets reales se omite cuando falta un escritorio.
En el entorno de preparación no hay pantalla gráfica, por lo que la apertura
visual queda por comprobar en tu WSLg. Las pruebas usan Atlas simulado; la primera
inserción real se verifica en tu laptop al pulsar Evaluar y guardar.

## Referencias

- [Tkinter y su modelo de eventos](https://docs.python.org/3/library/tkinter.html).
- [Inserción de documentos con PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/insert/).
- [Aplicaciones gráficas en WSL](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps).
