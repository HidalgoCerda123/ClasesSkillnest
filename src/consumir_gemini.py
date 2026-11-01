import os
import requests
from dotenv import load_dotenv

import time

import json
import re

load_dotenv()

#Constantes 
MODELO = "gemini-3.5-flash-lite"
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
API_KEY = os.getenv("GEMINI_API_KEY")

#funcion para crear la solicitud 
def armar_peticion(pregunta, modelo, system_instruction, response_schema=None): #pregunta= "Confirma la conexion"
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía.")
    url = f"{URL_BASE}{modelo}:generateContent?key={API_KEY}"
    body = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [{"parts": [{"text": pregunta}]}],
    }
    if response_schema is not None:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }

    return url, body
#arma_peticion_openai -> url, body

#funcion envia la peticion 
def enviar_peticion(url, body):
    try:
        respuesta= requests.post(url, json=body, timeout=120)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No se pudo conectar con el servicio. Intenta de nuevo en unos momentos.")
    except requests.exceptions.Timeout:
        raise RuntimeError("Se agoto el tiempo. Intenta de nuevo en unos momentos.")

    if respuesta.status_code in(401, 403):
         raise ValueError("Credencial invalida o sin permiso. Revisa tu GEMINI_API_KEY")
    if respuesta.status_code >= 500:
         raise TimeoutError("El proveedor no pudo procesar la peticion.Hay que esperar y reintentar")
    if respuesta.status_code == 429:
         segundos = respuesta.headers.get("Retry-After")
         mensaje = f"Limite excedido. Reintentar en {segundos}s." if segundos else "Limite excedido"
         raise TimeoutError(mensaje)

    if respuesta.status_code != 200:
        raise RuntimeError(f"Error en la solicitud. Status Code: {respuesta.status_code}. {respuesta.text}")
    
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llego en el formato esperado.") 

#funcion procesa y extrae dato 
def extraer_texto(datos):
    try: 
      return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La respuesta no recibe el texto generado en el lugar definido.")
    
def obtener_dato_prueba(pregunta):

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "categoria": {"type": "STRING"},
            "confianza": {"type": "NUMBER"}
        },
        "required": ["categoria", "confianza"]
    }
    system_instruction = "Eres un asistente amigable. Responde en máximo 2 palabras. Responde con un objerto JSON con la claves: 'categoria' y 'confianza' "
    url, body = armar_peticion(pregunta, MODELO, system_instruction, response_schema)

    inicio = time.perf_counter() #inicia contador de tiempo

    datos = enviar_peticion(url, body)
    fin = time.perf_counter() #termina contador de tiempo
    latencia= fin - inicio
    print(f"Latencia: {latencia:.2f} segundos")

    costo = calcular_costo(datos, 0.00000075, 0.00000375)
    print(f"Costo de la solicitud: ${costo:.6f} USD")
    texto = extraer_texto(datos)
    datos_formateados = parsear_respuesta_json(texto, ["categoria", "confianza"])
    return datos_formateados

def calcular_costo(datos, precio_entrada, precio_salida):
    uso = datos["usageMetadata"]
    tokens_entrada = uso.get("promptTokenCount", 0)
    tokens_salida = uso.get("candidatesTokenCount", 0)
    tokens_razonamiento = uso.get("thoughtsTokenCount", 0)
    costo = (tokens_entrada * precio_entrada) + ((tokens_salida + tokens_razonamiento) * precio_salida)
    return costo

def parsear_respuesta_json(texto, claves_requeridas):
    """
    claves_requeridas = ["categoria", "confianza"]
    """
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    try:
         datos = json.loads(texto_limpio)
    except json.JSONDecodeError as e:
        raise ValueError("la respuesta del modelo no es JSON valido")

    if claves_requeridas:
         faltantes = [clave for clave in claves_requeridas if clave not in datos]
         if faltantes:
                raise ValueError("La resúesta no tiene la estructura esperada.")
    return datos


if __name__ == "__main__":
        try:
                print(obtener_dato_prueba("Confirma en 2 palabras maximo que esta conexion funciona correctamente"))
        except (ValueError, RuntimeError) as error:
                print("No se pudo completar la petición: ", error)