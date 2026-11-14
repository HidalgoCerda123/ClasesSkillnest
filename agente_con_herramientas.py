import os
import time

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from src.consumir_gemini import MODELO

# Datos de ejemplo: en un sistema real vendrían de una base de datos.
TICKETS = {
    "T-1001": {
        "actual": "en revisión por el equipo técnico",
        "historial": ["creado", "asignado a soporte técnico", "en revisión"],
    },
    "T-1002": {
        "actual": "resuelto, a la espera de la confirmación del cliente",
        "historial": ["creado", "en revisión", "resuelto"],
    },
    "T-1003": {
        "actual": "escalado a un especialista",
        "historial": ["creado", "en revisión", "escalado"],
    },
}


# ======================= HERRAMIENTAS =================================

class ArgumentosConsultaTicket(BaseModel):
    numero_ticket: str = Field(
        description="Número del ticket de soporte, por ejemplo T-1001."
    )
    incluir_historial: bool = Field(
        default=False,
        description="Si es True, incluye el historial completo del ticket.",
    )


@tool("consultar_estado_ticket_con_historial", args_schema=ArgumentosConsultaTicket)
def consultar_estado_ticket(numero_ticket: str, incluir_historial: bool = False) -> str:
    """Úsala cuando el cliente pregunte en qué estado está su ticket o
    solicitud de soporte y mencione un número como T-1001. Si pide ver los
    pasos anteriores o el historial, activa incluir_historial."""
    try:
        numero = numero_ticket.strip().upper()
        ticket = TICKETS.get(numero)
        if ticket is None:
            return f"No se encontró ningún ticket con el número {numero_ticket}."
        if not incluir_historial:
            return f"El ticket {numero} está {ticket['actual']}."
        pasos = ", ".join(ticket["historial"])
        return f"El ticket {numero} está {ticket['actual']} (historial: {pasos})."
    except Exception as error:
        return f"No se pudo consultar el ticket: {error}"


class ArgumentosReembolso(BaseModel):
    precio: float = Field(description="Precio pagado por el producto, en pesos.")
    dias_desde_compra: int = Field(
        description="Cantidad de días que pasaron desde la compra."
    )


@tool("calcular_reembolso", args_schema=ArgumentosReembolso)
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


# ======================= AGENTE =======================================

prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system",
        "Eres un asistente de soporte que responde en español usando las "
        "herramientas disponibles cuando las necesites. Si la pregunta no "
        "requiere ninguna herramienta, responde directamente.",
    ),
    MessagesPlaceholder("chat_history"),
    ("human", "{entrada}"),
    MessagesPlaceholder("agent_scratchpad"),
])


def construir_ejecutor(modelo, herramientas=herramientas):
    """Arma el agente con sus herramientas; el modelo entra como parámetro."""
    agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)
    return AgentExecutor(
        agent=agente,
        tools=herramientas,
        verbose=True,
        return_intermediate_steps=True,
    )


# ======================= MEMORIA ======================================

historiales = {}


def obtener_historial(session_id: str):
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]


def cerrar_sesion(session_id: str):
    historiales.pop(session_id, None)


def extraer_texto_salida(salida):
    """Gemini puede devolver una lista de bloques; el historial necesita str."""
    if isinstance(salida, str):
        return salida
    return "".join(
        bloque.get("text", "") if isinstance(bloque, dict) else str(bloque)
        for bloque in salida
    )


def construir_agente_con_memoria(ejecutor_agente):
    ejecutor_con_texto = ejecutor_agente | RunnableLambda(
        lambda r: {**r, "output": extraer_texto_salida(r["output"])}
    )
    return RunnableWithMessageHistory(
        ejecutor_con_texto,
        obtener_historial,
        input_messages_key="entrada",
        history_messages_key="chat_history",
    )


def invocar(agente_con_memoria, entrada, session_id):
    config = {"configurable": {"session_id": session_id}}
    resultado = agente_con_memoria.invoke({"entrada": entrada}, config)
    longitud = len(obtener_historial(session_id).messages)
    print(f"[{session_id}] mensajes en el historial: {longitud}")
    time.sleep(6)  # evita superar el límite de peticiones por minuto
    return resultado


if __name__ == "__main__":
    load_dotenv()

    # La herramienta se prueba directo con .invoke() antes de conectarla.
    prueba_directa = consultar_estado_ticket.invoke(
        {"numero_ticket": "T-1001", "incluir_historial": True}
    )
    assert "historial" in prueba_directa
    print("Prueba directa de la herramienta:", prueba_directa)

    modelo = ChatGoogleGenerativeAI(
        model=MODELO, google_api_key=os.getenv("GEMINI_API_KEY")
    )
    agente_con_memoria = construir_agente_con_memoria(construir_ejecutor(modelo))

    # Elección de herramienta (cada prueba en su propia sesión).
    resultado = invocar(
        agente_con_memoria, "¿En qué estado está mi ticket T-1001?", "prueba_ticket"
    )
    assert resultado["intermediate_steps"][0][0].tool == "consultar_estado_ticket_con_historial"

    resultado = invocar(
        agente_con_memoria,
        "Compré algo de 50000 pesos hace 5 días y quiero devolverlo, "
        "¿cuánto me devuelven?",
        "prueba_reembolso",
    )
    assert resultado["intermediate_steps"][0][0].tool == "calcular_reembolso"

    resultado = invocar(
        agente_con_memoria, "¿Cuál es la capital de Chile?", "prueba_general"
    )
    assert resultado["intermediate_steps"] == []

    # Conversación de 2 turnos con el mismo session_id: el 2.º usa el contexto del 1.º.
    invocar(
        agente_con_memoria,
        "Dime el estado del ticket T-1001 con su historial",
        "cliente_123",
    )
    resultado = invocar(
        agente_con_memoria, "¿y ese mismo ticket ya fue resuelto?", "cliente_123"
    )
    usó_contexto = "T-1001" in str(resultado["intermediate_steps"]) or "T-1001" in resultado["output"]
    assert usó_contexto, "el 2.º turno no usó el contexto del 1.º"
    assert len(obtener_historial("cliente_123").messages) == 4

    # Aislamiento: dos session_id distintos no comparten historial.
    invocar(agente_con_memoria, "Mi ticket es el T-1002, ¿cómo va?", "cliente_1")
    invocar(agente_con_memoria, "¿Qué es un ticket de soporte?", "cliente_2")
    assert len(obtener_historial("cliente_1").messages) == 2
    assert len(obtener_historial("cliente_2").messages) == 2
    assert "T-1002" not in str(obtener_historial("cliente_2").messages)

    print("Todas las pruebas manuales pasaron.")
