"""Agente de soporte con supervisión humana y traza de decisión (Bloque 23).

Suma al agente de agente_con_herramientas.py una herramienta de riesgo alto
(generar_reembolso) que no se ejecuta sin aprobación humana, y deja registro
de cada decisión en trazas_agente.jsonl.

Ejecutar desde una terminal real: python agente_supervision.py
"""

import json
import os
import threading
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from agente_con_herramientas import (
    calcular_reembolso,
    construir_agente_con_memoria,
    construir_ejecutor,
    consultar_estado_ticket,
    invocar,
)
from src.consumir_gemini import MODELO

ARCHIVO_TRAZAS = "trazas_agente.jsonl"
ARCHIVO_APROBACIONES = "aprobaciones_agente.jsonl"

registro_aprobaciones = []


# ======================= APROBACIÓN HUMANA ============================

def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 300) -> bool:
    """Pide aprobación por teclado. Sin respuesta a tiempo = no aprobado.

    select.select() no funciona sobre stdin en Windows, así que la lectura
    va en un hilo aparte y el hilo principal espera con límite de tiempo.
    Si el tiempo se agota, el hilo queda esperando y consumirá la siguiente
    línea que se escriba: esa línea se descarta, nunca aprueba nada.
    """
    respuesta = []

    def leer():
        try:
            respuesta.append(input(mensaje))
        except EOFError:
            pass  # no hay stdin real: se trata como "sin respuesta"

    hilo = threading.Thread(target=leer, daemon=True)
    hilo.start()
    hilo.join(tiempo_limite_segundos)
    if hilo.is_alive() or not respuesta:
        return False
    return respuesta[0].strip().lower() == "s"


def registrar_aprobacion(herramienta: str, argumentos: dict, aprobado: bool) -> None:
    registro = {
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "momento": datetime.now().isoformat(),
    }
    registro_aprobaciones.append(registro)
    with open(ARCHIVO_APROBACIONES, "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


# ======================= HERRAMIENTA DE RIESGO ALTO ===================

class ArgumentosGenerarReembolso(BaseModel):
    numero_pedido: str = Field(description="Número del pedido a reembolsar, por ejemplo P-2001.")
    monto: float = Field(description="Monto a reembolsar, en pesos.")


@tool("generar_reembolso", args_schema=ArgumentosGenerarReembolso)
def generar_reembolso(numero_pedido: str, monto: float) -> str:
    """Genera (ejecuta) un reembolso para un pedido. Úsala solo cuando el
    cliente pida explícitamente que se le devuelva el dinero de un pedido y
    dé el número de pedido y el monto. Para saber cuánto correspondería,
    usa calcular_reembolso. Acción irreversible: requiere aprobación humana
    antes de ejecutarse."""
    mensaje = (
        f"\nEl agente quiere reembolsar ${monto} para el pedido "
        f"{numero_pedido}. ¿Aprobar? (s/n): "
    )
    aprobado = esperar_aprobacion(mensaje)
    registrar_aprobacion(
        "generar_reembolso", {"numero_pedido": numero_pedido, "monto": monto}, aprobado
    )
    if not aprobado:
        return "Reembolso no aprobado por el supervisor humano."
    return f"Reembolso de ${monto} generado para el pedido {numero_pedido}."


herramientas = [consultar_estado_ticket, calcular_reembolso, generar_reembolso]


# ======================= TRAZA DE DECISIÓN ============================

def registrar_traza(session_id: str, entrada: str, resultado: dict, archivo: str = ARCHIVO_TRAZAS) -> None:
    """Agrega una línea JSON con lo que el agente decidió en esta interacción."""
    acciones = [
        {
            "herramienta": accion.tool,
            "argumentos": accion.tool_input,
            "observacion": str(observacion),
        }
        for accion, observacion in resultado.get("intermediate_steps", [])
    ]
    traza = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": acciones,
        "respuesta_final": resultado["output"],
    }
    with open(archivo, "a", encoding="utf-8") as salida:
        salida.write(json.dumps(traza, ensure_ascii=False) + "\n")


def marcar_repeticiones_sospechosas(archivo: str = ARCHIVO_TRAZAS) -> list:
    """Devuelve las sesiones donde la misma herramienta aparece dos veces
    seguidas (solo se compara el nombre). Son candidatas para revisar a mano,
    no un veredicto."""
    try:
        with open(archivo, encoding="utf-8") as entrada:
            lineas = entrada.readlines()
    except FileNotFoundError:
        print(f"No existe {archivo}: todavía no se registró ninguna traza.")
        return []

    sospechosas = []
    for numero, linea in enumerate(lineas, start=1):
        if not linea.strip():
            continue
        try:
            traza = json.loads(linea)
        except json.JSONDecodeError:
            print(f"Línea {numero} de {archivo} corrupta: se omite.")
            continue
        anterior = None
        for accion in traza["acciones"]:
            if accion["herramienta"] == anterior:
                if traza["session_id"] not in sospechosas:
                    sospechosas.append(traza["session_id"])
                break
            anterior = accion["herramienta"]
    return sospechosas


def invocar_con_traza(agente_con_memoria, entrada: str, session_id: str) -> dict:
    resultado = invocar(agente_con_memoria, entrada, session_id)
    registrar_traza(session_id, entrada, resultado)
    return resultado


if __name__ == "__main__":
    load_dotenv()

    modelo = ChatGoogleGenerativeAI(
        model=MODELO, google_api_key=os.getenv("GEMINI_API_KEY")
    )
    agente_con_memoria = construir_agente_con_memoria(
        construir_ejecutor(modelo, herramientas)
    )

    # Riesgo bajo: solo lectura y solo cálculo.
    invocar_con_traza(
        agente_con_memoria, "¿En qué estado está mi ticket T-1001?", "demo_ticket"
    )
    invocar_con_traza(
        agente_con_memoria,
        "Compré algo de 50000 pesos hace 5 días, ¿cuánto me devolverían?",
        "demo_calculo",
    )

    # Riesgo alto: se detiene a pedir aprobación (responde s o n).
    for pedido, sesion in (("P-2001", "demo_reembolso_1"), ("P-2002", "demo_reembolso_2")):
        resultado = invocar_con_traza(
            agente_con_memoria,
            f"Genera el reembolso de 50000 pesos para mi pedido {pedido}.",
            sesion,
        )
        print("Respuesta final:", resultado["output"])

    print("Aprobaciones registradas:", registro_aprobaciones)
    print("Sesiones con repeticiones sospechosas:", marcar_repeticiones_sospechosas())
