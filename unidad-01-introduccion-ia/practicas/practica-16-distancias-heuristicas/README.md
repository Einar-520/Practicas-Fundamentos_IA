# Práctica 16 · Distancias Manhattan y Euclidiana

**Objetivo:** calcular y comparar ambas distancias entre **A = (1, 2)** y
**B = (5, 5)**, dibujar sus recorridos sobre el mismo plano y permitir cambiar
las coordenadas desde una interfaz gráfica.

## Desarrollo del ejercicio

Se utilizan los puntos escritos en el enunciado del alumno: A=(1,2), B=(5,5).
La fotografía contiene también otros ejemplos; no reemplazan estos valores.

```text
Δx = |xB - xA| = |5 - 1| = 4
Δy = |yB - yA| = |5 - 2| = 3

Manhattan:  hM = |xB - xA| + |yB - yA| = 4 + 3 = 7
Euclidiana: hE = √((xB - xA)² + (yB - yA)²) = √(16 + 9) = 5
```

El recorrido Manhattan mide **7 unidades** y la línea recta **5 unidades**.
La diferencia es **2 unidades**. Los valores son distancias del plano; coinciden
con costos únicamente si cada unidad recorrida cuesta una unidad de costo.

- **Manhattan:** se representa A → (5,2) → B, primero horizontal y luego vertical.
- **Euclidiana:** se representa el segmento recto A → B.
- También puede dibujarse A → (1,5) → B: cambiar el orden de los ejes no cambia
  la longitud Manhattan. Son dos ejemplos entre varios recorridos mínimos.

## Tabla de diferencias

| Concepto | Manhattan | Euclidiana |
| --- | --- | --- |
| Movimiento | Por los ejes X e Y; horizontal y vertical | Directo entre los puntos, en cualquier dirección |
| Fórmula | `abs(xB-xA) + abs(yB-yA)` | `sqrt((xB-xA)² + (yB-yA)²)` |
| Fundamento | Suma de longitudes por coordenadas; norma L1 | Teorema de Pitágoras; norma L2 |
| Geometría de puntos a igual distancia | Rombo o diamante | Circunferencia |
| Ejercicio A=(1,2), B=(5,5) | 7 unidades | 5 unidades |
| Uso como heurística | Cuadrícula con movimientos por ejes y costo unitario | Estimación en línea recta si los costos respetan las distancias geométricas |
| Relación | Mayor o igual que Euclidiana | Menor o igual que Manhattan |

**El rombo no es la ruta entre A y B:** es la forma del conjunto de puntos
a una distancia Manhattan fija de un centro. En Euclidiana ese conjunto es
una circunferencia. Si A y B comparten X o Y, las dos distancias son iguales.
Si son el mismo punto, ambas valen cero.

Estas medidas no consideran obstáculos ni costos adicionales de calles.
Para utilizarlas en A*, h(n) debe corresponder al objetivo, a los movimientos
permitidos y a las unidades de los costos. Por ejemplo, Manhattan puede
sobreestimar si se permiten diagonales baratas.

## Preparar y ejecutar en VS Code con WSL

Requiere **Python 3.10 o posterior**, Tkinter y Matplotlib para la ventana.
Desde la raíz de `fundamentos-ia`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-16-distancias-heuristicas/requirements.txt
bash unidad-01-introduccion-ia/practicas/practica-16-distancias-heuristicas/ejecutar.sh
```

El lanzador usa `.venv/bin/python` cuando existe; de lo contrario, `python3`.
Selecciona ese mismo intérprete en VS Code. Si ya tienes `.venv`, basta con
instalar las dependencias y ejecutar el lanzador.

Si falta Tkinter en Ubuntu/WSL:

```bash
sudo apt install python3-tk
```

La interfaz necesita soporte gráfico WSLg. Para calcular solamente, sin
Matplotlib ni Tkinter:

```bash
bash unidad-01-introduccion-ia/practicas/practica-16-distancias-heuristicas/ejecutar.sh --terminal
```

Para generar la imagen sin abrir una ventana:

```bash
bash unidad-01-introduccion-ia/practicas/practica-16-distancias-heuristicas/ejecutar.sh --sin-ventana
```

La imagen se guarda en `salidas/Comparacion_distancias.png`, dentro de esta
práctica. Cada ejecución con la misma ruta reemplaza esa imagen. Usa `--salida`
para elegir otro archivo:

```bash
bash unidad-01-introduccion-ia/practicas/practica-16-distancias-heuristicas/ejecutar.sh --a -2 1 --b 3 4 --orden yx --salida /tmp/otros_puntos.png
```

`--a X Y` y `--b X Y` también permiten abrir la interfaz con otros puntos.
`--orden xy` dibuja primero X; `--orden yx`, primero Y.

## Uso de la interfaz

1. La ventana comienza con A=(1,2), B=(5,5) y muestra los resultados 7 y 5.
2. Cambia las cuatro coordenadas y pulsa **Calcular** o Enter.
3. Observa las dos líneas, los puntos etiquetados, Δx y Δy, y el desarrollo de
   las fórmulas en el panel lateral. La escala física de X e Y es la misma.
4. Cambia el orden del recorrido Manhattan con el selector. La distancia se conserva.
5. Abre **Tabla de diferencias** para consultar las tres columnas comparativas.
6. Pulsa **Guardar gráfica PNG** para elegir una ubicación, o **Restablecer**
   para recuperar los puntos del ejercicio.

Los campos admiten negativos y decimales con punto o coma. Se rechazan vacíos,
texto, NaN, infinitos y distancias que desborden. El visor limita las coordenadas
a **[-1000000, 1000000]** por estabilidad y legibilidad; ese límite no pertenece
a las fórmulas y no se aplica al modo de solo cálculo en terminal.

Cuando editas un campo, la ventana avisa que hay cambios pendientes y mantiene
la última gráfica válida hasta que pulses Calcular. La exportación se habilita
cuando los valores son válidos. Los números mostrados se redondean a seis cifras
significativas; los cálculos usan la precisión de `float`.

En puntos alineados las líneas coinciden: se conserva una línea naranja gruesa
y una azul discontinua para poder distinguir ambas. Los puntos iguales se
etiquetan A=B y se evita un rango de ejes vacío.

## Organización del código

| Archivo | Responsabilidad |
| --- | --- |
| `distancias.py` | Validación, distancias, recorrido por ejes y resultados |
| `grafica_distancias.py` | Matplotlib, escala igual y exportación PNG |
| `16_distancias_heuristicas.py` | Interfaz Tkinter, tabla, entradas y comandos |
| `requirements.txt` | Dependencia Matplotlib |
| `ejecutar.sh` | Inicio con el intérprete del proyecto |
| `test_distancias.py` | Propiedades matemáticas y fidelidad de las líneas dibujadas |

`math.hypot(dx, dy)` implementa la distancia Euclidiana evitando algunos
desbordamientos de elevar al cuadrado. Las dos distancias se calculan con
la misma pareja de puntos, sin sumar valores heurísticos ni pesos de los grafos
de prácticas anteriores. Esta práctica es independiente.

Se revisaron los dos scripts del RAR `14_10_2026_practicas.rar`:
`p30algoritmosbusquedacompara.py` y `p30heuristica2.py`. Son ejemplos de búsquedas
sobre grafos; el ejercicio de distancias se desarrolla en esta carpeta a partir
del enunciado y la fotografía.

## Verificación

```bash
.venv/bin/python -m unittest discover -s unidad-01-introduccion-ia/practicas/practica-16-distancias-heuristicas -p 'test_*.py' -v
```

Las pruebas comprueban el resultado 7/5, simetría, traslación, coordenadas
negativas, puntos iguales y alineados, ambas rutas Manhattan, datos inválidos,
desbordamientos y la longitud real de las líneas que Matplotlib dibuja.

## Referencias de implementación

- [Matplotlib: integrar una figura en Tkinter](https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_tk_sgskip.html).
- [Matplotlib: escala de los ejes con set_aspect](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.set_aspect.html).
