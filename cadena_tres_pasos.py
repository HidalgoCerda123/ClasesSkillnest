import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.consumir_gemini import MODELO


def construir_cadena(modelo):
    """Arma la chain extraer puntos -> redactar respuesta -> revisar tono.

    Recibe el modelo como parámetro (así las pruebas pueden inyectar un mock)
    y devuelve la chain sin ejecutarla.
    """
    # Paso 1: extrae del mensaje del cliente los problemas concretos.
    extraer_puntos = PromptTemplate.from_template(
        "Lee el mensaje de un cliente y lista, en viñetas cortas y sin "
        "agregar nada nuevo, cada problema o petición concreta que plantea.\n\n"
        "Mensaje del cliente:\n{mensaje}"
    )

    # Paso 2: redacta la respuesta de soporte a partir de esos puntos.
    redactar_respuesta = PromptTemplate.from_template(
        "Eres un agente de soporte. Redacta una respuesta al cliente que "
        "atienda uno por uno los siguientes puntos:\n\n{puntos}"
    )

    # Paso 3: corrige el tono del borrador.
    revisar_tono = PromptTemplate.from_template(
        "Reescribe este borrador con un tono empático y profesional, sin "
        "promesas que no se puedan cumplir y en máximo 80 palabras. "
        "Responde solo con el texto final.\n\nBorrador:\n{borrador}"
    )

    parser = StrOutputParser()

    paso_1 = extraer_puntos | modelo | parser
    paso_2 = redactar_respuesta | modelo | parser
    paso_3 = revisar_tono | modelo | parser

    # Las lambdas envuelven cada string en la clave que espera el siguiente template.
    return (
        paso_1
        | (lambda puntos: {"puntos": puntos})
        | paso_2
        | (lambda borrador: {"borrador": borrador})
        | paso_3
    )


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(
        model=MODELO, google_api_key=os.getenv("GEMINI_API_KEY")
    )
    cadena = construir_cadena(modelo)
    resultado = cadena.invoke({
        "mensaje": (
            "Hola, hace dos semanas compré una notebook en su tienda en línea "
            "y llegó con la pantalla rota. Escribí al soporte el lunes y me "
            "dijeron que me contactarían en 48 horas, pero nadie me ha "
            "respondido. Además me cobraron el despacho dos veces. Necesito "
            "que me cambien el equipo o me devuelvan el dinero, y que alguien "
            "me explique por qué nadie respondió."
        )
    })
    print(resultado)
