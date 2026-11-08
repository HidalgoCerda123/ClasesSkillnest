import os

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from src.consumir_gemini import MODELO

# Datos de ejemplo: en un sistema real vendrían de una base de datos.
TICKETS = {
    "T-1001": "en revisión por el equipo técnico",
    "T-1002": "resuelto, a la espera de la confirmación del cliente",
    "T-1003": "escalado a un especialista",
}


@tool
def consultar_estado_ticket(numero_ticket: str) -> str:
    """Úsala cuando el cliente pregunte en qué estado está su ticket o
    solicitud de soporte y mencione un número como T-1001."""
    try:
        estado = TICKETS.get(numero_ticket.strip().upper())
        if estado is None:
            return f"No se encontró ningún ticket con el número {numero_ticket}."
        return f"El ticket {numero_ticket.strip().upper()} está {estado}."
    except Exception as error:
        return f"No se pudo consultar el ticket: {error}"


@tool
def calcular_reembolso(precio: float, dias_desde_compra: int) -> str:
    """Úsala cuando el cliente pregunte cuánto dinero le devolverían al
    devolver un producto, dando el precio pagado y los días desde la compra."""
    try:
        if precio < 0 or dias_desde_compra < 0:
            return "El precio y los días desde la compra no pueden ser negativos."
        if dias_desde_compra <= 10:
            porcentaje = 100
        elif dias_desde_compra <= 30:
            porcentaje = 80
        else:
            return "Han pasado más de 30 días: ya no corresponde reembolso."
        monto = precio * porcentaje / 100
        return f"Corresponde un reembolso del {porcentaje}%: ${monto:.0f}."
    except Exception as error:
        return f"No se pudo calcular el reembolso: {error}"


herramientas = [consultar_estado_ticket, calcular_reembolso]

prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system",
        "Eres un asistente de soporte que responde en español usando las "
        "herramientas disponibles cuando las necesites. Si la pregunta no "
        "requiere ninguna herramienta, responde directamente.",
    ),
    ("human", "{entrada}"),
    MessagesPlaceholder("agent_scratchpad"),
])


def construir_ejecutor(modelo):
    """Arma el agente con sus herramientas; el modelo entra como parámetro."""
    agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)
    return AgentExecutor(
        agent=agente,
        tools=herramientas,
        verbose=True,
        return_intermediate_steps=True,
    )


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(
        model=MODELO, google_api_key=os.getenv("GEMINI_API_KEY")
    )
    ejecutor_agente = construir_ejecutor(modelo)

    # Prueba 1: debe usar consultar_estado_ticket
    resultado = ejecutor_agente.invoke(
        {"entrada": "¿En qué estado está mi ticket T-1001?"}
    )
    assert resultado["intermediate_steps"][0][0].tool == "consultar_estado_ticket"

    # Prueba 2: debe usar calcular_reembolso
    resultado = ejecutor_agente.invoke({
        "entrada": "Compré algo de 50000 pesos hace 5 días y quiero "
                   "devolverlo, ¿cuánto me devuelven?"
    })
    assert resultado["intermediate_steps"][0][0].tool == "calcular_reembolso"

    # Prueba 3: una pregunta general no debe usar ninguna herramienta
    resultado = ejecutor_agente.invoke({"entrada": "¿Cuál es la capital de Chile?"})
    assert resultado["intermediate_steps"] == []

    print("Las 3 pruebas manuales confirmaron la elección de herramienta.")
