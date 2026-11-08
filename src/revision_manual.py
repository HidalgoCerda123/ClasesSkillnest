import json

# Muestra: los 5 casos con f1 más bajo y los 5 con f1 más alto de
# docs/resultados_metricas.json (20 respuestas generadas con consultar_modelo).
revision_manual = [

    # --- f1 más bajo ---
    {
        "consulta": "¿Cuál es la diferencia entre una lista y una tupla en Python?",
        "f1": 0.09,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "respuesta correcta; el f1 es mínimo porque usa plurales y "
            "sinónimos (mutables/modificables, inmutables/fijas) que no "
            "coinciden con 'mutable' e 'inmutable' de la referencia"
        ),
    },
    {
        "consulta": "¿Cuándo se creó Python?",
        "f1": 0.27,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "el año 1991 es correcto; el f1 baja porque agrega 'oficialmente' "
            "y '20 de febrero', palabras que no están en la referencia"
        ),
    },
    {
        "consulta": "¿Para qué sirve Git?",
        "f1": 0.27,
        "correccion_factual": "si",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": (
            "explica bien el propósito pero con otras palabras: no usa "
            "'control de versiones' y agrega 'trabajo colaborativo'"
        ),
    },
    {
        "consulta": "¿Qué es una variable en programación?",
        "f1": 0.32,
        "correccion_factual": "si",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": (
            "no menciona que la variable tiene un nombre, que es parte de la "
            "referencia; agrega que el valor puede cambiar, que es cierto"
        ),
    },
    {
        "consulta": "¿Qué significa HTTP?",
        "f1": 0.40,
        "correccion_factual": "si",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": (
            "describe para qué sirve el protocolo pero no desarrolla la sigla: "
            "falta 'hipertexto', que era lo que preguntaba la consulta"
        ),
    },

    # --- f1 intermedio, agregado por un fallo de formato ---
    {
        "consulta": "¿Cuál es la fórmula química del agua?",
        "f1": 0.50,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "H2O correcto, pero el modelo lo escribió como $H_2O$ (LaTeX): "
            "tras la limpieza queda 'h_2o' y no coincide con 'h2o' de la "
            "referencia; además agrega la explicación de los átomos"
        ),
    },

    # --- f1 más alto ---
    {
        "consulta": "¿En qué año llegó el ser humano a la Luna?",
        "f1": 0.90,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "año 1969 correcto; solo agrega 'el año', sin cambiar el sentido",
    },
    {
        "consulta": "¿Cuál es el río más largo de Sudamérica?",
        "f1": 0.90,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Amazonas correcto; agrega 'caudaloso', dato verdadero y no contradictorio",
    },
    {
        "consulta": "¿Cuántos planetas tiene el sistema solar?",
        "f1": 0.86,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "ocho planetas correcto; solo agrega 'en total'",
    },
    {
        "consulta": "¿Qué es una lista en Python?",
        "f1": 0.76,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "coincide con la referencia (ordenada y modificable) y agrega "
            "'elementos heterogéneos', que es correcto"
        ),
    },
    {
        "consulta": "¿Quién creó Python?",
        "f1": 0.74,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "Guido van Rossum correcto; agrega 'neerlandés' y 'en 1991', "
            "ambos datos verdaderos"
        ),
    },

]


if __name__ == "__main__":
    with open(
        "docs/revision_manual.json", "w", encoding="utf-8"
    ) as archivo:
        json.dump(
            revision_manual, archivo, indent=2, ensure_ascii=False
        )
    print(f"{len(revision_manual)} casos guardados en docs/revision_manual.json")
