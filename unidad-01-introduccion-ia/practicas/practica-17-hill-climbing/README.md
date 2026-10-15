# Práctica 17: Hill Climbing

**Objetivo:** maximizar un valor mediante búsqueda local. En cada paso se
comparan los vecinos del estado actual, se elige el mejor y se avanza solamente
si su valor es estrictamente mayor. Se detiene cuando ningún vecino mejora.

Programa independiente con Python, **Tkinter y Matplotlib**. Incluye los dos
ejercicios del profesor, salida en terminal y exportación de las gráficas a PNG.
No necesita MongoDB, Ollama ni otra práctica.

## 1. Recorrido de una lista

Datos: `2, 5, 8, 12, 9, 6, 3`. El estado es una posición y sus vecinos son las
posiciones inmediatamente a la izquierda y a la derecha. La función que se
maximiza es el valor de esa posición.

| Paso | Posición, desde 1 | Valor | Decisión |
| --- | --- | --- | --- |
| 0 | 1 | 2 | Estado inicial |
| 1 | 2 | 5 | 5 mejora a 2 |
| 2 | 3 | 8 | 8 mejora a 5 |
| 3 | 4 | 12 | 12 mejora a 8 |

Se detiene en **12**, tras **3 movimientos**, porque sus vecinos 8 y 9 son
menores. En este caso también es el máximo global de la lista. No se salta
directamente al mayor valor ni se ordenan los datos antes de buscar.

La ventana permite editar la lista y la posición inicial. En caso de empate
entre dos vecinos mejores, se elige el de menor índice. Un vecino con el mismo
valor que el actual no permite avanzar: no hay pasos laterales.

## 2. Selección de productos

Presupuesto: **$1,000 pesos**. Se interpreta que hay **una unidad disponible
de cada producto**. Los beneficios se expresan en unidades, ya que la tabla no
indica que sean importes en pesos.

| Producto | Costo en pesos | Beneficio |
| --- | ---: | ---: |
| A | 200 | 30 |
| B | 300 | 50 |
| C | 400 | 70 |
| D | 250 | 40 |
| E | 350 | 60 |

El estado es un conjunto de productos. La función objetivo es la suma de sus
beneficios y la restricción es que la suma de los costos no supere el presupuesto.
Un vecino se obtiene al agregar uno, retirar uno o intercambiar un producto
seleccionado por uno disponible. Los vecinos se generan uno a uno.

Se elige el vecino factible que más aumenta el beneficio. Los empates entre
vecinos se resuelven por menor costo y después por los nombres de los productos.
**No se acepta un movimiento con beneficio igual o inferior al actual.**

| Paso | Selección | Costo | Beneficio |
| --- | --- | ---: | ---: |
| 0 | Ninguno | $0 | 0 |
| 1 | C | $400 | 70 |
| 2 | C, E | $750 | 130 |
| 3 | C, D, E | $1,000 | 170 |

**Mejor selección: C, D y E.** Costo total: $1,000; beneficio total: **170**;
presupuesto restante: $0. Se mantiene el orden alfabético para presentar cada
conjunto; el producto agregado en el último paso es D.

## Máximo local frente a máximo global

Hill Climbing no garantiza encontrar la mejor solución de todo el espacio.
El programa conserva esa limitación y la hace visible. Para responder cuáles
son los mejores productos, una **comprobación independiente** recorre los
`2⁵ = 32` subconjuntos, de los que 25 cumplen el presupuesto de $1,000.
Confirma que C, D y E es la única selección con beneficio 170.

La comprobación no guía los pasos de Hill Climbing ni modifica su resultado.
Muestra todas las selecciones que empatan en el beneficio global máximo,
ordenadas por costo y nombres. Se limita a 20 productos porque su trabajo crece
exponencialmente; la aplicación utiliza únicamente los cinco del ejercicio.

Dos ejemplos reproducibles de un máximo local:

- Lista `2, 5, 4, 12`, inicio en la posición 1: se detiene en **5**, aunque existe 12.
- Mismos productos, presupuesto **$850**, inicio vacío: Hill Climbing termina
  con C y E, costo $750 y beneficio **130**. La comprobación encuentra A, B, E
  o A, C, D, ambos con costo $850 y beneficio **140**. Llegar a ellos requiere
  cambiar más de lo permitido por un único vecino o aceptar primero una pérdida.

## Ejecutar en VS Code con WSL

Desde la raíz del proyecto:

```bash
cd ~/universidad/fundamentos-ia
git pull --ff-only origin main
python3 -m venv .venv
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-17-hill-climbing/requirements.txt
bash unidad-01-introduccion-ia/practicas/practica-17-hill-climbing/ejecutar.sh
```

Necesita Python 3.10 o posterior. La interfaz de escritorio necesita Tkinter y
WSLg. Si falta Tkinter en Ubuntu, instala `sudo apt install python3-tk` para el
Python utilizado. Selecciona `.venv/bin/python` como intérprete en VS Code.

La ventana incluye dos pestañas, tablas de pasos, posición inicial editable,
presupuesto editable y casillas para elegir la selección inicial. **Buscar**
recalcula la pestaña actual; **Restablecer** recupera los datos del profesor.
Las casillas representan el punto de partida, no el resultado final.

La gráfica de productos muestra en verde los elegidos por Hill Climbing;
la línea punteada muestra el beneficio global verificado. Los costos aparecen
bajo los nombres de los productos para no mezclar pesos con beneficio en el eje Y.
El botón **Guardar ambas gráficas PNG** exporta una imagen con los dos ejercicios.

Se validan números finitos, posición inicial, presupuesto no negativo y selección
inicial factible. Un campo inválido conserva el último resultado válido y muestra
un mensaje. Si hay cambios pendientes, se desactiva la exportación hasta recalcular.

### Terminal y ejecución sin pantalla

```bash
# Solo cálculos: no requiere Tkinter ni Matplotlib.
bash unidad-01-introduccion-ia/practicas/practica-17-hill-climbing/ejecutar.sh --terminal

# Cálculos y archivo salidas/Hill_Climbing.png, sin abrir ventanas.
bash unidad-01-introduccion-ia/practicas/practica-17-hill-climbing/ejecutar.sh --sin-ventana

# Mostrar las dos situaciones de máximo local.
bash unidad-01-introduccion-ia/practicas/practica-17-hill-climbing/ejecutar.sh --terminal --lista '2,5,4,12' --presupuesto 850

# Otra posición de inicio y selección inicial; exportar a una ruta elegida.
bash unidad-01-introduccion-ia/practicas/practica-17-hill-climbing/ejecutar.sh --inicio 7 --seleccion A,B --salida salidas/otro_inicio.png
```

La lista admite de 1 a 40 valores entre -1,000,000 y 1,000,000 para mantener legible
la gráfica. Usa comas para separar valores y punto para decimales. El presupuesto
se escribe en pesos enteros, sin `$` ni separadores de miles; cero es válido.

## Organización y memoria

| Archivo | Responsabilidad |
| --- | --- |
| `hill_climbing.py` | Datos, validación, búsqueda local y verificación exhaustiva separada |
| `17_hill_climbing.py` | Interfaz Tkinter, mensajes y opciones de terminal |
| `graficas.py` | Gráficas Matplotlib y exportación PNG sin pantalla |
| `test_hill_climbing.py` | Pruebas de resultados, restricciones y máximos locales |
| `ejecutar.sh` | Usa el entorno virtual de la raíz si existe |

El algoritmo local necesita conservar el estado actual y el mejor vecino; no
mantiene una frontera de búsqueda como BFS. Su memoria depende del tamaño de
un estado. Esta versión didáctica **también conserva la traza** para mostrar los
pasos y graficarlos; por ello la aplicación completa no tiene memoria constante.
La comprobación exhaustiva es un cálculo adicional, adecuado para este catálogo
pequeño. La ventaja de la búsqueda local es su bajo consumo de memoria; su
limitación principal son los máximos locales y las mesetas.

## Verificación

```bash
python3 -m unittest discover -s unidad-01-introduccion-ia/practicas/practica-17-hill-climbing -p 'test_*.py' -v
```

Las pruebas comprueban el recorrido original, búsqueda hacia ambos lados,
mesetas, empates, el óptimo 170 y el máximo local con presupuesto 850. También
revisan la mejora estricta y la factibilidad desde todas las selecciones iniciales
factibles para varios presupuestos, contrastadas con un oráculo de máscaras binarias.

Referencia conceptual: Poole y Mackworth, *Artificial Intelligence: Foundations
of Computational Agents*, [búsqueda local y mejora iterativa](https://www.cs.ubc.ca/~poole/aibook/3e/html/ArtInt3e.Ch4.S6.html).
Esta práctica usa la variante estricta solicitada: se detiene cuando no hay mejora.
