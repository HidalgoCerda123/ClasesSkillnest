# Límites de autonomía: agente de soporte (tickets y reembolsos)

Describe el agente tal como está hoy en `agente_supervision.py` (que reutiliza las herramientas y la memoria de `agente_con_herramientas.py`), no una versión ideal.

## Herramientas y nivel de riesgo

- `consultar_estado_ticket_con_historial`: **bajo**. Solo lee el diccionario de tickets; si el agente se equivoca, lo peor que pasa es que informa un estado incorrecto y se corrige volviendo a consultar.
- `calcular_reembolso`: **bajo**. Solo calcula un porcentaje y un monto; no devuelve dinero ni guarda nada.
- `generar_reembolso`: **alto**. Devuelve dinero al cliente y no se puede deshacer; un monto o pedido equivocado es una pérdida económica directa. Requiere aprobación humana.

El agente no tiene hoy ninguna herramienta de riesgo medio (escritura reversible).

Limitación conocida: `generar_reembolso` está simulada. Devuelve el mensaje de confirmación pero no se conecta a ningún sistema de pagos, y no valida que el pedido exista ni que el monto coincida con lo que entregaría `calcular_reembolso`. Esa validación hoy depende solo del supervisor humano.

## Herramientas que requieren aprobación humana

- `generar_reembolso`: mueve dinero de forma irreversible. Antes de ejecutarse llama a `esperar_aprobacion(`, que muestra el pedido y el monto y espera una respuesta por teclado.
  - Solo la respuesta `s` aprueba. Cualquier otra respuesta, la falta de respuesta en 300 segundos o la ausencia de teclado (`EOFError`) cuentan como **no aprobado**.
  - Cada decisión, aprobada o no, queda en `aprobaciones_agente.jsonl` con herramienta, argumentos, resultado y momento.
  - Limitación en Windows: como `select.select()` no funciona sobre el teclado, la lectura va en un hilo aparte. Si el tiempo se agota, ese hilo sigue esperando y se traga la siguiente línea que se escriba en esa terminal. Esa línea se descarta y nunca aprueba el reembolso vencido.

Las dos herramientas de riesgo bajo se ejecutan sin aprobación, a propósito: pedirla para todo llevaría a aprobar por costumbre.

Comprobado con `grep -n "esperar_aprobacion(" agente_supervision.py`: la única herramienta de riesgo alto la llama (línea 91).

## Revisión de trazas

Cada interacción hecha con `invocar_con_traza` agrega una línea a `trazas_agente.jsonl` con la hora (UTC), la sesión, la entrada, las acciones (herramienta, argumentos, observación) y la respuesta final. Las interacciones lanzadas desde `agente_con_herramientas.py` no dejan traza.

- Frecuencia: una vez por semana, una muestra de 10 trazas al azar, más **todas** las trazas donde aparece `generar_reembolso`.
- Qué se busca:
  - La misma herramienta dos veces seguidas en una sesión. Lo detecta `marcar_repeticiones_sospechosas()`, que compara solo el nombre y entrega candidatas para mirar a mano, no un veredicto.
  - Un `generar_reembolso` en la traza sin su línea correspondiente en `aprobaciones_agente.jsonl` (mismo pedido y monto). Hoy se cruza a mano; no hay función que lo haga.
  - Una respuesta final que afirme un reembolso generado cuando la observación dice "no aprobado", o que cite un estado de ticket o un monto que no aparece en ninguna observación (posible invención). También se revisa a mano.
  - Un `generar_reembolso` cuyo monto no coincide con lo que el cliente pidió en la entrada.

Estado real al 14-11-2026: el archivo tiene 4 trazas de una corrida de demostración (una consulta de ticket, un cálculo y dos `generar_reembolso`: uno aprobado y uno rechazado). `marcar_repeticiones_sospechosas()` no marcó ninguna sesión. Todavía no se ha hecho ninguna revisión semanal.

## Qué hacer ante un comportamiento inesperado

1. Si involucra `generar_reembolso`: sacarla de la lista `herramientas` en `agente_supervision.py` y reiniciar el agente. Queda funcionando solo con las dos herramientas de riesgo bajo.
2. Copiar las líneas de la sesión afectada de `trazas_agente.jsonl` y `aprobaciones_agente.jsonl` antes de tocar nada, para no perder la evidencia.
3. Leer la traza de esa sesión y ubicar el punto del fallo: herramienta equivocada, argumentos equivocados, o respuesta final que no coincide con la observación.
4. Según lo encontrado:
   - Herramienta equivocada: ajustar la descripción (docstring) de la herramienta que se confundió, por ejemplo la frontera entre `calcular_reembolso` (cuánto correspondería) y `generar_reembolso` (ejecutarlo).
   - Argumentos equivocados: ajustar las descripciones de los campos en su `args_schema`.
   - Respuesta que no coincide con la observación: ajustar el mensaje de sistema en `prompt_agente` para que responda solo con lo que devuelven las herramientas.
5. Repetir la entrada que falló y revisar la traza nueva. Correr `pytest test_agente_supervision.py`.
6. Reactivar `generar_reembolso` solo cuando la entrada que falló se comporte bien, y revisar todas sus trazas durante la semana siguiente.
7. Si se llegó a aprobar un reembolso incorrecto: avisar a quien administra los pagos con el pedido, el monto y el momento que figuran en `aprobaciones_agente.jsonl`. El agente no puede revertirlo.
