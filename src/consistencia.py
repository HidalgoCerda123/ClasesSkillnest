import json
import time
from src.prompts.banco import BANCO_DE_PROMPT
from src.consumir_gemini import MODELO, armar_peticion, enviar_peticion, extraer_texto, parsear_respuesta_json

registro = {}

try:
    for prompt in BANCO_DE_PROMPT:
        exitos = 0
        intentos = 3
        for intento in range(intentos):
            url, body = armar_peticion(
                prompt["ejemplo_usuario"],
                MODELO,
                prompt["system_instruction"],
                prompt["response_schema"],
            )
            try:
                respuesta = enviar_peticion(url, body)
                texto = extraer_texto(respuesta)
                datos = parsear_respuesta_json(texto, prompt["claves_esperadas"])
                exitos += 1
                print(f"[{prompt['nombre']}] {datos}")
            except (ValueError, RuntimeError) as error:
                print(f"intento {intento + 1} fallo: {error}")
            time.sleep(1)

        print(f"{prompt['nombre']}: {exitos}/{intentos} respuestas validas")
        registro[prompt["nombre"]] = {"exitos": exitos, "intentos": intentos}

    with open("src/prompts/registro_resultados.json", "w", encoding="utf-8") as archivo:
        json.dump(registro, archivo, indent=2, ensure_ascii=False)

except (ValueError, RuntimeError) as error:
    print("no se pudo completar la opertacion:", error)