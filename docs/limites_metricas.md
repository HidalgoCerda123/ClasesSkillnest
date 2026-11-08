# Límites de la métrica de evaluación

## Qué mide

Compara, palabra por palabra, la respuesta del modelo con una referencia corta: tras pasar a minúsculas y quitar la puntuación, cuenta cuántas palabras exactas aparecen en ambos textos (sin importar el orden ni el significado). La precisión es coincidencias sobre las palabras de la respuesta, la cobertura es coincidencias sobre las palabras de la referencia, y el F1 es su media armónica.

## Modos de falla conocidos

- **Una respuesta correcta con otras palabras puntúa casi cero.** La métrica no reconoce plurales ni sinónimos. Ejemplo: "¿Cuál es la diferencia entre una lista y una tupla en Python?", F1 = 0.09. La referencia dice "mutable" e "inmutable" y la respuesta, igual de correcta, dice "mutables", "modificables", "inmutables" y "fijas".
- **Agregar datos verdaderos baja la precisión.** Cada palabra extra cuenta como error aunque sea cierta. Ejemplo: "¿Cuándo se creó Python?", F1 = 0.27. El año 1991 es correcto, pero la respuesta agrega "oficialmente" y "20 de febrero". Lo mismo en "¿Para qué sirve Git?", F1 = 0.27.
- **El formato del modelo rompe coincidencias que sí existían.** Ejemplo: "¿Cuál es la fórmula química del agua?", F1 = 0.50. El modelo escribió `$H_2O$` en LaTeX; tras la limpieza queda `h_2o`, que no coincide con `h2o` de la referencia, aunque el dato es el mismo.
- **Un F1 bajo no distingue entre "incorrecto", "incompleto" y "bien dicho distinto".** En la muestra, tres respuestas parcialmente completas ("¿Qué significa HTTP?", F1 = 0.40, no desarrolla la sigla; "¿Qué es una variable en programación?", F1 = 0.32, omite que tiene nombre; "¿Para qué sirve Git?", F1 = 0.27, no dice "control de versiones") puntuaron parecido a respuestas correctas y completas como "¿Cuándo se creó Python?" (0.27). El número solo no permite separarlas.
- **No observado en esta muestra:** una respuesta con F1 alto pero incorrecta. Las 5 respuestas de F1 más alto resultaron correctas y completas. El riesgo teórico (cambiar un dato manteniendo la oración) no lo pude comprobar con mis datos, así que no lo afirmo como hallazgo.

## Muestra revisada

Se generaron 20 respuestas con `consultar_modelo` (preguntas cortas de datos y definiciones, con la instrucción de responder en una sola oración de máximo 15 palabras) y se guardaron en `docs/resultados_metricas.json`. Ronda del 2026-11-08. Se revisaron a mano 11 casos, registrados en `docs/revision_manual.json` (generado por `src/revision_manual.py`): los 5 de F1 más bajo, los 5 de F1 más alto y 1 intermedio, el del agua, incluido por el fallo de formato. Cada uno se calificó con tres preguntas (sí / no / parcialmente): corrección factual, completitud y contradicción, con una nota de justificación.

Resultado: los 11 casos fueron factualmente correctos y ninguno contradijo la referencia. Solo 3 resultaron parcialmente completos (HTTP, variable y Git). De los 5 de F1 más bajo, 2 eran respuestas totalmente correctas y completas (lista vs tupla y "¿Cuándo se creó Python?").

## Recomendación de uso

Para este pipeline (preguntas cortas, referencias de una oración y respuestas breves):

- Un F1 alto (desde 0.74 en la muestra) coincidió con respuestas correctas, pero solo en preguntas de dato corto. Sirve como señal razonable, no como prueba.
- Un F1 bajo no significa que la respuesta esté mal: las 5 más bajas eran correctas y 2 de ellas además completas. No debe usarse para rechazar respuestas automáticamente.
- Usa el F1 para decidir qué revisar a mano (los casos bajos), no para aprobar ni rechazar.
- Revisa siempre a mano cuando la pregunta pida una sigla, un nombre, una fecha o una cifra, y cuando la respuesta incluya formato (LaTeX, listas).
- Antes de confiar más en el número, conviene normalizar plurales y formato (por ejemplo quitar `$` y `_`) y buscar activamente un caso de F1 alto con dato incorrecto.
