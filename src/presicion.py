from collections import Counter
from src.pipeline_limpieza import *
from src.cliente import *
import json
import time

PAUSA_ENTRE_CONSULTAS = 6  # segundos, para no superar el límite de peticiones por minuto

def contar_coincidencias(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> int:
    """Cuenta las coincidencias entre referencia y respuesta."""
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    interseccion = conteo_referencia & conteo_respuesta
    return sum(interseccion.values())

def calcular_precision_cobertura_f1(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> dict[str, float]:
    """Calcula precisión, cobertura y F1 de dos listas de tokens."""
    coincidencias = contar_coincidencias(
        tokens_referencia, tokens_respuesta
    )

    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    precision = coincidencias / len(tokens_respuesta)
    cobertura = coincidencias / len(tokens_referencia)

    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)

    resultado = {
        "precision": precision,
        "cobertura": cobertura,
        "f1": f1,
    }

    return resultado

def calcular_metricas(texto_referencia, texto_respuesta):

    tokens_referencia = procesar_texto(texto_referencia)
    tokens_respuesta = procesar_texto(texto_respuesta)
    return calcular_precision_cobertura_f1(
        tokens_referencia, tokens_respuesta
    )

casos = [

    (
        "¿Qué es Python?",
        "Python es un lenguaje de programación interpretado.",
    ),

    ("¿Cuándo se creó Python?", "Python fue creado en 1991."),

    (
        "¿Qué es una lista en Python?",
        "Una lista es una colección ordenada y modificable.",
    ),

    ("¿Quién creó Python?", "Python fue creado por Guido van Rossum."),

    ("¿En qué año se lanzó Python 3.0?", "Python 3.0 se lanzó en 2008."),

    (
        "¿En qué año llegó el ser humano a la Luna?",
        "El ser humano llegó a la Luna en 1969.",
    ),

    (
        "¿Python es un lenguaje compilado?",
        "No, Python es un lenguaje interpretado.",
    ),

    ("¿Cuál es la capital de Chile?", "La capital de Chile es Santiago."),

    (
        "¿Cuál es la fórmula química del agua?",
        "La fórmula química del agua es H2O.",
    ),

    (
        "¿Cuántos planetas tiene el sistema solar?",
        "El sistema solar tiene ocho planetas.",
    ),

    (
        "¿Cuál es el planeta más grande del sistema solar?",
        "El planeta más grande del sistema solar es Júpiter.",
    ),

    (
        "¿Cuál es el río más largo de Sudamérica?",
        "El río más largo de Sudamérica es el Amazonas.",
    ),

    (
        "¿Qué significa HTTP?",
        "HTTP significa protocolo de transferencia de hipertexto.",
    ),

    (
        "¿Qué es una variable en programación?",
        "Una variable es un espacio con nombre que almacena un valor.",
    ),

    (
        "¿Qué es una función en Python?",
        "Una función es un bloque de código reutilizable que se define con def.",
    ),

    (
        "¿Qué es un diccionario en Python?",
        "Un diccionario es una colección de pares clave valor.",
    ),

    (
        "¿Para qué sirve Git?",
        "Git es un sistema de control de versiones que registra los cambios del código.",
    ),

    (
        "¿Qué es una API?",
        "Una API es una interfaz que permite que dos programas se comuniquen.",
    ),

    (
        "¿Cuál es la diferencia entre una lista y una tupla en Python?",
        "Una lista es mutable y una tupla es inmutable.",
    ),

    (
        "¿Por qué el cielo es azul?",
        "El cielo es azul porque la atmósfera dispersa más la luz azul del Sol.",
    ),

]



resultados = []

for consulta, referencia in casos:
    respuesta = consultar_modelo(consulta, system_instruction= "Responde en español con una definicion breve, una sola oracion de maximo 15 palabras. sin listas, ejemplos ni introducciones.")
    metricas = calcular_metricas(referencia, respuesta)
    print("Consulta:", consulta)
    print("Respuesta:",respuesta)
    print("Metricas:", metricas)

    resultados.append({
        "consulta": consulta,
        "respuesta": respuesta,
        **metricas,
    })
    time.sleep(PAUSA_ENTRE_CONSULTAS)


with open(
    "docs/resultados_metricas.json", "w", encoding="utf-8"
) as archivo:

    json.dump(resultados, archivo, indent=2, ensure_ascii=False)

def resumir_metricas(resultados):

    if not resultados:
        return {
            "precision_promedio": 0,
            "cobertura_promedio": 0,
            "f1_promedio": 0,
        }

    n = len(resultados)

    return {
        "precision_promedio": sum(
            r["precision"] for r in resultados
        ) / n,

        "cobertura_promedio": sum(
            r["cobertura"] for r in resultados
        ) / n,

        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }

print("Promedios")
print(resumir_metricas(resultados))

peores_casos = sorted(resultados, key=lambda r: r["f1"])

for caso in peores_casos[:3]:

    print(caso["consulta"], caso["f1"])
#referencia = procesar_texto( "Python es un lenguaje de programación interpretado.")

#texto_respuesta = consultar_modelo("¿Qué es Python?", system_instruction="Responde en español con una definicion breve, en una sola oracion de maximo 15 palabras. sin listas, ejemplos ni introducciones.")
#respuesta = procesar_texto(texto_respuesta)

#resultado = calcular_precision_cobertura_f1(referencia, respuesta)
#print("Respuesta:", texto_respuesta)
#print("Tokens de referencia:", len(referencia))
#print("Tokens de respuesta :", len(respuesta))
#print(resultado)
