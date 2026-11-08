import os
import time

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableBranch, RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

from src.consumir_gemini import MODELO

# Clasifica un mensaje de soporte en una sola palabra.
plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de soporte en UNA sola palabra: "
    "pregunta, queja o sugerencia. Responde únicamente con esa palabra, "
    "en minúsculas y sin puntuación.\n\nMensaje: {mensaje}"
)

# Ruta por defecto: respuesta técnica y precisa.
plantilla_pregunta = PromptTemplate.from_template(
    "Eres un agente técnico de soporte. Responde de forma precisa y "
    "concreta la pregunta del cliente, con pasos numerados si hacen falta. "
    "Máximo 60 palabras.\n\nPregunta: {mensaje}"
)

# Ruta de queja: empatía primero, solución después.
plantilla_queja = PromptTemplate.from_template(
    "Eres un agente de soporte empático. Primero reconoce el problema y la "
    "molestia del cliente con tus propias palabras, y solo después ofrece "
    "una solución concreta, sin prometer plazos que no puedas cumplir. "
    "Máximo 60 palabras.\n\nQueja: {mensaje}"
)

# Ruta de sugerencia: agradecer y explicar cómo se evaluará.
plantilla_sugerencia = PromptTemplate.from_template(
    "Eres un agente de soporte. Agradece la sugerencia del cliente y explica "
    "cómo se evaluará (revisión del equipo de producto y prioridad según "
    "impacto), sin garantizar que se implementará. Máximo 60 palabras."
    "\n\nSugerencia: {mensaje}"
)


def construir_paso_clasificacion(modelo):
    return (
        plantilla_clasificacion
        | modelo
        | StrOutputParser()
        | (lambda t: t.strip().lower())
    )


def construir_rutas(modelo):
    """Arma las tres cadenas de respuesta: queja, sugerencia y pregunta."""
    parser = StrOutputParser()
    cadena_queja = plantilla_queja | modelo | parser
    cadena_sugerencia = plantilla_sugerencia | modelo | parser
    cadena_pregunta = plantilla_pregunta | modelo | parser
    return cadena_queja, cadena_sugerencia, cadena_pregunta


def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_queja=None,
    cadena_sugerencia=None,
    cadena_pregunta=None,
):
    cadena_queja = cadena_queja or RunnablePassthrough()
    cadena_sugerencia = cadena_sugerencia or RunnablePassthrough()
    cadena_pregunta = cadena_pregunta or RunnablePassthrough()

    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "queja", cadena_queja),
        (lambda x: x["categoria"] == "sugerencia", cadena_sugerencia),
        cadena_pregunta,  # ruta por defecto: cualquier otra categoría cae aquí
    )
    return RunnablePassthrough.assign(categoria=paso_clasificacion) | bifurcacion


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(
        model=MODELO, google_api_key=os.getenv("GEMINI_API_KEY")
    )
    paso_clasificacion = construir_paso_clasificacion(modelo)
    cadena_queja, cadena_sugerencia, cadena_pregunta = construir_rutas(modelo)
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion, cadena_queja, cadena_sugerencia, cadena_pregunta
    )

    mensajes = [
        "¿Cómo puedo cambiar la contraseña de mi cuenta?",
        "Llevo tres días sin poder entrar a mi cuenta y nadie me responde.",
        "Sería genial que la aplicación tuviera modo oscuro.",
    ]
    for mensaje in mensajes:
        categoria = paso_clasificacion.invoke({"mensaje": mensaje})
        respuesta = cadena.invoke({"mensaje": mensaje})
        print(f"Mensaje:   {mensaje}")
        print(f"Categoría: {categoria}")
        print(f"Respuesta: {respuesta}\n")
        time.sleep(5)  # evita superar el límite de peticiones por minuto
