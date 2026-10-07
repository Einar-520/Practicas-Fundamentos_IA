# Guion breve de exposición

## Preparación previa

Descarga los cambios; instala dependencias; comprueba el navegador, MongoDB y
Ollama; descarga el modelo. Revisa manualmente el corpus y ejecuta la evaluación
real antes de clase. Conserva su archivo de resultados y el nombre del modelo.
Usa datos ficticios para que ninguna captura exponga información del conductor
o credenciales. Mantén el `.env` fuera de las capturas.

## Demostración en seis pasos

1. **Tutor de SQL.** Abre el ejercicio 1 en localhost:8011, pregunta cómo consultar una tabla,
   realiza una segunda pregunta y pulsa Resumen de mi historial. Explica el
   cambio de mensaje `system` respecto al tutor de IA original.
2. **MongoDB y camiones.** Abre el ejercicio 2 en localhost:8012 en modo MongoDB; verifica conexión,
   registra o consulta CAM-102 y enseña la misma colección en Compass.
3. **Reglas de acceso.** Busca la placa de CAM-102. Activa P/S/R, desactiva Q y
   mantén H verdadero/T falso: A y E son verdaderos, pero la decisión final es
   inspección. Guarda y muestra la explicación. En el simulador cambia H o T para
   demostrar las dos reglas nuevas y sus tablas.
4. **Incidentes y evaluación.** Pega un correo de derrame, clasifícalo, revisa el
   JSON validado y modifica su estado. Enseña historial y un intento de LLM.
   Abre los resultados de tus 30 correos revisados y compara los tres métodos;
   señala errores y latencias, incluyendo el grupo con escritura informal.
5. **Asistente con evidencia.** Pregunta «¿por qué CAM-102 fue enviado a inspección?».
   Abre el acceso citado. Pregunta después por CAM-999 sin registros y muestra
   «No tengo información». Después pide «Genera un informe de los camiones que
   fueron rechazados y sus motivos». Muestra el total de accesos, camiones únicos,
   motivos y fuentes; descarga el PDF desde el chat. Explica que estos informes se
   calculan con los registros guardados, funcionan sin Ollama y no cambian accesos.
6. **Ética y reportes.** Muestra riesgos de alucinación, sesgo, privacidad y
   automatización, con puntajes antes/después. Exporta un PDF y el JSON de un
   reporte. Cierra mostrando el enlace al repositorio y la arquitectura por capas.

## Si un servicio falla durante la exposición

- MongoDB: informa el fallo; comprueba conexión y permisos. Para mostrar la GUI
  puedes abrir `--demo`, indicando claramente que usa un archivo local.
- Ollama: comprueba el servidor/modelo. Muestra el respaldo por reglas y la marca
  de revisión humana; no lo presentes como una respuesta del LLM.
- Nunca sustituyas resultados no medidos por cifras inventadas. Usa el archivo
  de una ejecución real guardada y explica cuándo y con qué modelo se obtuvo.
