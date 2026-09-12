# Progreso - Fundamentos de Inteligencia Artificial

Este archivo registra únicamente los temas y herramientas que ya he visto
en clase o que aparecen directamente en mis apuntes.

No debe agregarse contenido avanzado por inferencia.

---

# Unidad 1 - Introducción a la Inteligencia Artificial

Estado: EN CURSO

## Historia de la Inteligencia Artificial

Visto hasta ahora:

- 1950: Alan Turing propone que las máquinas pueden pensar.
- 1956: creación del término Inteligencia Artificial.
- 1970: empiezan los primeros sistemas.
- 1980: se congela el desarrollo de la IA.
- 1990: se dan a conocer los sistemas expertos.
- 1990: segundo invierno de la IA.
- 2000 - 2012: nace el aprendizaje profundo basado en las redes neuronales.
- 2012 - 2026: pendiente de verificación (el rango aparece en los apuntes
  sin descripción legible).

Pendiente de verificación:

- En la línea "2000 - 2012" hay una palabra ilegible entre "basado" y
  "de las redes neuronales".

---

# Definición de Inteligencia Artificial

Concepto visto:

La Inteligencia Artificial es la disciplina que se encarga de diseñar
agentes computacionales capaces de percibir su entorno, analizar lo
recibido y actuar en pro de alcanzar un objetivo, imitando o igualando
capacidades inteligentes como los seres humanos.

Pendiente de verificación:

- El final de la palabra "capacidades" está borroso en el apunte.

---

# Agentes

Conceptos vistos:

- Agente.
- Entorno.
- Sensores.
- Actuadores.

Un agente es cualquier entidad que percibe su entorno mediante sensores
y actúa mediante actuadores.

---

# PEAS

Se ha visto el concepto PEAS.

Elementos registrados en los apuntes (tal como aparecen escritos):

- Performance.
- Enviroment.
- Actuadores.
- Sources.

Pendiente de verificación:

- "Enviroment" está escrito así en el apunte.
- El cuarto elemento se lee "Sources"; podría estar destinado a decir
  "Sensors", pero se conserva tal como aparece en el apunte.

Este tema todavía puede ampliarse durante la unidad.

---

# Tipos de entornos

Vistos (agrupados por dimensión, como en los apuntes):

- Observabilidad: Totalmente / Parcialmente.
- Determinismo: Determinista / Estocástico.
- Episodios / secuencial.
- Cambio: Estático / Dinámico.
- Agente o Multiagente.

---

# Enfoques de la Inteligencia Artificial

Vistos:

- Pensar como humano.
- Pensar racionalmente.
- Actuar como humano.
- Actuar racionalmente.

---

# Lógica proposicional

Conceptos vistos:

- Lógica proposicional.
- Proposición.
- Valores verdadero (V) y falso (F).

La lógica proposicional es el lenguaje formal más simple con el que
una máquina puede razonar. Es el fundamento de los sistemas expertos.

Una proposición tiene un valor: V o F.

Ejemplo de proposiciones visto en los apuntes:

- P = Alumno estudia.
- Q = Alumno aprueba.

---

# Conectores lógicos

Vistos:

## Negación

Símbolo en los apuntes:

¬

## Conjunción

Símbolo en los apuntes:

∧ (se lee "Y")

## Disyunción

Símbolo en los apuntes:

∨ (se lee "O")

## Condicional

Símbolo en los apuntes:

→

## Bicondicional

Símbolo en los apuntes:

↔

Pendiente de verificación:

- Los símbolos están escritos a mano y en tamaño pequeño; la lectura
  de ∧, ∨, → y ↔ es una interpretación.

---

# Tablas de verdad

Se ha visto:

- Tabla de verdad: herramienta para evaluar todas las combinaciones
  posibles de V y F.

## Tarea 01 - Tablas de verdad (indicada por el profesor en el pizarrón)

- Para dos proposiciones P y Q hay 2^2 = 4 combinaciones posibles
  (VV, VF, FV, FF).
- Se construyó la tabla de verdad combinada de:
  - ¬P
  - P ∧ Q
  - P ∨ Q
  - P → Q  (rotulado como "Si entonces" en el pizarrón)
  - P ↔ Q
- Resuelta en:
  `unidad-01-introduccion-ia/tareas/tarea-01-tablas-verdad/tablas_verdad.py`

Pendiente de verificación:

- El encabezado de la última columna del pizarrón está escrito muy
  pequeño; se interpretó como P ↔ Q por sus valores (V, F, F, V).
- Los valores de la columna P ∨ Q en la foto están algo borrosos; se
  asumió el patrón estándar V, V, V, F.

---

# Precedencia de operadores lógicos

Orden de evaluación según los apuntes:

1. Paréntesis.
2. Negación (es el primero que se evalúa).
3. Conjunción.
4. Disyunción.
5. Condicional.
6. Bicondicional.

Pendiente de verificación:

- Confirmar si este es el orden completo y definitivo o si el profesor
  lo ampliará.

---

# Python

Nivel actual: BÁSICO

Conceptos utilizados en clase:

- Variables.
- Asignación de valores.
- input().
- float().
- lower().
- print().
- Comparaciones.
- Operadores de comparación >= y == (vistos en el ejercicio).
- Guardar el resultado de una comparación en una variable
  (ejemplo: P = Asistencia >= 80).
- Valores booleanos.
- Operador lógico and (visto en: Resultado = P and Q and R).
- if.
- if que evalúa una variable booleana (ejemplo: if resultado:).
- else.

Conceptos utilizados en la Tarea 01 (tablas de verdad):

- Asignar directamente True o False a una variable (ejemplo: P = True).
- Comparar dos variables booleanas con == (ejemplo: P == Q).
- if / else sobre una variable booleana para asignar en cada rama
  el valor que corresponde.
- print() con varios valores separados por comas en la misma línea
  (ejemplo: print(P, "|", Q)).

Ejemplos de valores o variables utilizados:

- Asistencia.
- Promedio.
- Proyecto_F.
- Resultado.
- Proposiciones nombradas P, Q, R, F.

Pendiente de verificación:

- En el apunte hay una cuarta variable de entrada cuyo nombre está
  tachado / ilegible (posiblemente relacionada con "Deal").
- Aparece una anotación "Dataset = []" cuyo propósito no queda claro
  en el apunte.

Todavía NO asumir conocimientos avanzados de Python.

---

# Herramientas del curso

Nota: los datos de versión de esta sección se toman del entorno
instalado (carpeta 00-entorno/), no de los apuntes. En los apuntes
solo aparece la anotación "Instalar WSL, SPARK, Mongo, PY".

## WSL

Estado:

CONFIGURADO

Entorno actual:

- WSL 2.
- Ubuntu 24.04.

---

## Visual Studio Code

Estado:

CONFIGURADO

Se utiliza conectado a:

WSL Ubuntu 24.04

---

## Python

Estado:

CONFIGURADO

Versión actual:

Python 3.12.3

El proyecto utiliza un entorno virtual:

.venv/

---

## Java

Estado:

CONFIGURADO

Versión:

OpenJDK 17

Se utiliza como dependencia para Apache Spark.

---

## Apache Spark / PySpark

Estado:

INSTALADO

Versión actual:

Apache Spark / PySpark 4.2.0

IMPORTANTE:

Tener Spark instalado no significa que ya se hayan visto sus conceptos
en clase.

Actualmente no se consideran aprendidos temas como:

- Spark SQL.
- DataFrames.
- RDD.
- MLlib.
- Streaming.
- Clusters.

Estos temas se habilitarán únicamente cuando aparezcan en clase.

---

## MongoDB

Estado:

INSTALADO

Versiones actuales:

- MongoDB Server 8.0.29.
- Mongosh 2.10.0.

Actualmente MongoDB está instalado y funcionando.

Esto NO significa que ya se hayan visto consultas o conceptos avanzados
de MongoDB.

---

## Claude Code

Estado:

INSTALADO

Versión actual:

Claude Code 2.1.259

Claude Code debe seguir las instrucciones definidas en:

CLAUDE.md

---

# Temas aún no habilitados

No considerar como conocimientos actuales:

- Machine Learning.
- Deep Learning.
- Redes neuronales en implementación.
- Scikit-learn.
- TensorFlow.
- PyTorch.
- Pandas.
- NumPy.
- Spark SQL.
- MLlib.
- MongoDB avanzado.
- APIs.
- Programación orientada a objetos avanzada.

Aunque alguno de estos temas pueda mencionarse de forma general,
no utilizarlo para resolver ejercicios hasta que aparezca en clase.

Nota: "aprendizaje profundo" y "redes neuronales" aparecen mencionados
en la línea de tiempo histórica de los apuntes, pero NO se han estudiado
ni habilitado como técnica.

---

# Forma de actualizar este archivo

Cuando se agreguen nuevos apuntes:

1. Revisar los apuntes nuevos.
2. Identificar únicamente los conceptos realmente vistos.
3. Agregar esos conceptos a la unidad correspondiente.
4. No agregar conceptos relacionados por inferencia.
5. Mantener el nivel de Python, Spark y MongoDB acorde con la clase.
6. Actualizar el estado de la unidad cuando corresponda.

---

# Estado actual del curso

Unidad actual:

Unidad 1 - Introducción a la Inteligencia Artificial

Estado:

EN CURSO
