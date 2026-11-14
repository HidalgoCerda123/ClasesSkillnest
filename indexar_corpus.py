"""Indexa el corpus de la miniaplicación en Chroma (Bloque 24).

Se ejecuta una sola vez (o cuando cambia el corpus): python indexar_corpus.py
Las consultas posteriores se reconectan con Chroma(persist_directory=...)
sin volver a calcular embeddings (ver verificar_vectorstore.py).
"""

import os
import shutil

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DIRECTORIO_VECTORSTORE = "vectorstore/"
MODELO_EMBEDDINGS = "models/gemini-embedding-001"

# Se usa RecursiveCharacterTextSplitter porque el corpus es documentación en
# párrafos: corta primero en "\n\n", luego en "\n" y en espacios, así cada
# chunk conserva una idea completa. CharacterTextSplitter con tamaño fijo
# partiría palabras y mezclaría, por ejemplo, el manejo del 429 con el del 401.
# 300 caracteres alcanza para un párrafo corto del corpus (una idea por chunk);
# el solapamiento de 50 (~17 %) mantiene el contexto cuando un párrafo se parte.
TAMANO_CHUNK = 300
SOLAPAMIENTO_CHUNK = 50

# Corpus: extractos de la documentación de la miniaplicación de soporte.
CORPUS = {
    "manejo_de_errores": (
        "Manejo de errores del cliente de Gemini. La función enviar_peticion "
        "traduce cada fallo HTTP a una excepción de Python con un mensaje claro.\n\n"
        "Un estado 401 o 403 lanza ValueError: la credencial es inválida o no "
        "tiene permiso, y hay que revisar GEMINI_API_KEY. Este error no se "
        "reintenta porque repetir la llamada no lo arregla.\n\n"
        "Un estado 429 (límite de peticiones excedido) o un estado 500 o "
        "superior lanza TimeoutError: el problema es temporal y conviene "
        "esperar y reintentar. Si la respuesta trae el encabezado Retry-After, "
        "el mensaje indica cuántos segundos esperar.\n\n"
        "Un fallo de conexión, un tiempo agotado de 120 segundos o una "
        "respuesta que no es JSON lanzan RuntimeError."
    ),
    "reintentos": (
        "Reintentos con espera exponencial. La función con_reintento ejecuta "
        "una llamada hasta 3 veces y solo reintenta ante RuntimeError o "
        "TimeoutError.\n\n"
        "La espera se duplica en cada intento: 2 segundos, luego 4, con un "
        "máximo de 30 segundos. A cada espera se le suma hasta un 10 % "
        "aleatorio (jitter) para que varios clientes no reintenten al mismo "
        "tiempo.\n\n"
        "Si el último intento también falla, consultar_modelo lanza "
        "RuntimeError con el mensaje: el servicio no respondió tras varios "
        "intentos, intenta más tarde."
    ),
    "calculo_de_costo": (
        "Cálculo de costo de cada petición. La función calcular_costo lee "
        "usageMetadata de la respuesta de Gemini y multiplica los tokens de "
        "entrada por el precio de entrada, y los tokens de salida más los de "
        "razonamiento por el precio de salida.\n\n"
        "Los precios usados en la prueba son 0.00000075 dólares por token de "
        "entrada y 0.00000375 dólares por token de salida.\n\n"
        "La función registrar_costo del cliente modular usa una estimación "
        "más simple: 0.002 dólares por cada 1000 tokens totales, y acumula el "
        "costo de toda la sesión en costo_total_sesion."
    ),
    "enrutamiento": (
        "Enrutamiento condicional de mensajes de soporte. Un primer paso "
        "clasifica cada mensaje en una sola palabra: pregunta, queja o "
        "sugerencia.\n\n"
        "Según la categoría, RunnableBranch elige la cadena de respuesta. La "
        "queja se responde con empatía primero y solución después. La "
        "sugerencia se agradece y se explica cómo se evaluará. Cualquier otra "
        "categoría cae en la ruta por defecto, que responde como pregunta "
        "técnica.\n\n"
        "Si la cadena de queja falla, un fallback devuelve un mensaje "
        "genérico: un miembro del equipo te va a responder pronto. Si falla "
        "cualquier otra parte, procesar_mensaje_seguro registra el error y "
        "responde que no se pudo procesar el mensaje."
    ),
    "agente": (
        "Qué hace el agente de soporte. El agente decide por sí mismo qué "
        "herramienta usar y recuerda la conversación de cada cliente por su "
        "session_id con RunnableWithMessageHistory.\n\n"
        "Tiene tres herramientas. consultar_estado_ticket_con_historial "
        "informa el estado de un ticket como T-1001 y, si se pide, su "
        "historial. calcular_reembolso calcula cuánto se devolvería: 100 % "
        "hasta 10 días desde la compra, 80 % hasta 30 días y nada después.\n\n"
        "generar_reembolso ejecuta el reembolso de un pedido. Es de riesgo "
        "alto porque mueve dinero de forma irreversible, así que no se "
        "ejecuta sin aprobación humana. Sin respuesta en 300 segundos, el "
        "reembolso queda como no aprobado.\n\n"
        "Cada interacción queda registrada en trazas_agente.jsonl con la "
        "entrada, las herramientas usadas, sus observaciones y la respuesta "
        "final."
    ),
    "pruebas": (
        "Qué cubren las pruebas. Las pruebas se ejecutan con pytest y no "
        "llaman a la API real: usan modelos y funciones simuladas.\n\n"
        "tests/test_cliente.py cubre los reintentos del cliente y el registro "
        "de costo. test_enrutamiento.py comprueba que cada categoría llegue a "
        "su ruta y que la categoría desconocida use la ruta por defecto.\n\n"
        "test_orquestacion.py cubre el manejo de errores de las cadenas, "
        "incluido el fallback de la ruta de queja. test_agente_supervision.py "
        "comprueba que el reembolso solo se apruebe con la respuesta s, que "
        "el silencio cuente como no aprobado y que la traza se escriba bien."
    ),
    "limites_de_la_metrica": (
        "Límites de la métrica de evaluación. La métrica compara palabra por "
        "palabra la respuesta del modelo con una referencia corta y calcula "
        "precisión, cobertura y F1.\n\n"
        "Una respuesta correcta dicha con otras palabras puntúa casi cero, "
        "porque la métrica no reconoce plurales ni sinónimos. Agregar datos "
        "verdaderos baja la precisión.\n\n"
        "Por eso un F1 bajo no significa que la respuesta esté mal. El F1 se "
        "usa para decidir qué casos revisar a mano, no para aprobar ni "
        "rechazar respuestas automáticamente."
    ),
}


def crear_chunks(corpus: dict = CORPUS) -> list[Document]:
    """Parte cada documento en chunks; cada uno recuerda de qué documento viene."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=TAMANO_CHUNK, chunk_overlap=SOLAPAMIENTO_CHUNK
    )
    return splitter.create_documents(
        list(corpus.values()),
        metadatas=[{"documento": nombre} for nombre in corpus],
    )


def crear_embeddings() -> GoogleGenerativeAIEmbeddings:
    load_dotenv()
    clave = os.getenv("GEMINI_API_KEY")
    if not clave:
        raise SystemExit("Falta GEMINI_API_KEY en el archivo .env.")
    return GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS, google_api_key=clave)


if __name__ == "__main__":
    chunks = crear_chunks()
    for chunk in chunks:
        print(f"{len(chunk.page_content):>4} caracteres | {chunk.metadata['documento']}")

    embeddings = crear_embeddings()

    # from_documents agrega a lo que ya exista: se borra el índice anterior
    # para que re-indexar no duplique chunks.
    shutil.rmtree(DIRECTORIO_VECTORSTORE, ignore_errors=True)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DIRECTORIO_VECTORSTORE,
    )
    print(f"Indexados {len(chunks)} chunks de {len(CORPUS)} documentos en {DIRECTORIO_VECTORSTORE}")
