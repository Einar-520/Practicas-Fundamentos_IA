# Matriz de requisitos y evidencia

La columna «implementación» identifica dónde se desarrolla cada punto. La
verificación con sustitutos locales no equivale a una prueba contra Atlas u Ollama.

| Requisito | Implementación / acceso en GUI | Evidencia y estado |
| --- | --- | --- |
| Cambiar sistema del primer tutor | `tutor/servicio.py`, `MENSAJE_SISTEMA` | Especialista en SQL y biblioteca escolar, distinto del tutor de IA original. |
| GUI del tutor | `tutor/interfaz.py` | Chat, Enviar, Resumen, Exportar, Nueva conversación. |
| Resumen del historial | `TutorSQL.resumir()` | LLM sobre últimas seis interacciones; respaldo local identificado. Historial persistente y exportable. |
| Arquitectura por capas | `logismart/dominio`, `servicios`, `infraestructura`, `presentacion` | Dominios sin importaciones de Tkinter ni MongoDB. |
| Cinco colecciones mínimas | `infraestructura/repositorio.py` | camiones, accesos, incidentes, riesgos_eticos, evaluaciones_llm. |
| CRUD desde GUI | `presentacion/formularios.py` y `componentes.py` | Alta/consulta/edición/baja de las cinco; bajas lógicas con evidencia conservada. |
| Agregación MongoDB | `MongoRepositorio.agregar_incidentes()` | `$match`, `$group`, `$isoWeekYear`, `$isoWeek`, `$sort`. Adaptador demo calcula el equivalente local. |
| Errores de conexión | Repositorio y `comun/ollama_local.py` | Mensajes sin URL con contraseña; respaldo LLM explícito; no cambio automático de base. |
| A y E originales | `dominio/reglas.py` | Tabla independiente con las 16 combinaciones y prueba del caso A=E=V. |
| Dos reglas nuevas | B=R∧¬H y F=P∧T | Justificación y tablas completas en informe/simulador. |
| Decisiones persistidas | `Aplicacion.guardar_acceso()` | P/Q/R/S/H/T, A/E/B/F, fecha, operador, explicación y decisión final. |
| JSON del LLM | `Clasificacion`, `Entidades` | Claves exactas, tipos estrictos, rangos, categorías cerradas; extra prohibido. |
| Reintento y respaldo | `ClasificadorHibrido.clasificar()` | Un reintento ante JSON inválido; si sigue inválido o falla conexión, reglas y revisión humana. |
| Fusión conservadora | `fusionar()` | Prevalece mayor prioridad; en empate categoría de reglas; discrepancias requieren revisión. |
| 30 correos etiquetados | `datos/correos_etiquetados.json` | 30 sintéticos con etiquetas propuestas; **pendiente confirmación humana** mediante GUI. |
| Métricas de tres métodos | `servicios/evaluacion.py` | Exactitud, matriz, cobertura y latencias. Línea base real incluida; **Ollama real pendiente**. |
| Asistente RAG y fuentes | `servicios/asistente.py` | Consulta primero, selección de fuentes validadas y respuesta literal con origen. |
| Ausencia de datos | `responder()` | «No tengo información» sin consulta LLM si no existe contexto; prueba incluida. |
| Riesgos de implementación | `RIESGOS_DEMO` | Seis riesgos, incluidos alucinación, sesgo informal, privacidad y automatización. |
| Riesgo inicial/residual | CRUD Riesgos y gráfica Matplotlib | Probabilidad × impacto antes/después; histórico y campo evidencia. |
| Panel y filtros | `VentanaLogiSmart._panel()` | Camiones únicos, accesos, incidentes abiertos, riesgos residuales críticos; fechas UTC. |
| Acceso y semáforo | Formulario de accesos | Búsqueda por placa, P/S calculados a partir del registro, explicación en vivo. |
| Simulador | `VentanaLogiSmart._tablas()` | Interruptores y tres tablas; simulación sin escritura. |
| Bandeja y estados | Página Incidentes | Correo original conservado, clasificación editable, estados e historial. |
| Chat con historial | Página Asistente | Consultas y fuentes en evaluaciones_llm; botón Cargar historial. |
| PDF/CSV/JSON | `servicios/reportes.py` | Exportación por colección/período; CSV protege contra fórmulas. |
| Configuración | Página Configuración | Modelo, timeout, uso LLM, operador, horario, umbral y simulación de correo. |
| Usabilidad | `TrabajosTk`, formularios y tablas | Validación, progreso durante red/LLM, confirmación de baja y control de cambios concurrentes. |
| Datos demo | `servicios/demostracion.py` | 17 registros ficticios, carga idempotente; no inventa evaluaciones LLM. |
| Informe técnico | `docs/INFORME_TECNICO.md` | Arquitectura, contratos, prompts, línea base y análisis ético. |
| Exposición | `docs/EXPOSICION.md` | Preparación y demostración en seis pasos. |

## Pendientes para la entrega final evaluada por el profesor

1. Confirmar manualmente las 30 etiquetas y guardar el corpus revisado.
2. Comprobar MongoDB real con el usuario/base autorizados y verificar CRUD y
   agregación desde la GUI/Compass.
3. Ejecutar tutor, clasificación y asistente con el modelo real instalado en Ollama.
4. Ejecutar la comparación de los tres métodos y anexar su JSON y conclusiones
   al informe. No usar la línea base sola como si fuera esa comparación.

El código de estos pasos está implementado; las verificaciones que dependen de
la infraestructura del alumno deben quedar documentadas con su ejecución real.
