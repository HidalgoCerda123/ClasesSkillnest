"""Comprueba que la clave y el modelo de embeddings funcionan (Bloque 24)."""

from indexar_corpus import crear_embeddings

if __name__ == "__main__":
    embeddings = crear_embeddings()  # termina con SystemExit si falta la clave

    # Solo se protege la llamada externa.
    try:
        vector = embeddings.embed_query("¿Cómo maneja la aplicación un error 429?")
    except Exception as error:
        texto = str(error)
        if "429" in texto or "RESOURCE_EXHAUSTED" in texto:
            print("Límite de peticiones excedido: espera un minuto y vuelve a intentar.")
        elif any(codigo in texto for codigo in ("401", "403", "API_KEY_INVALID", "PERMISSION_DENIED")):
            print("Clave inválida o sin permiso: corrige GEMINI_API_KEY en .env.")
        else:
            print(f"Error inesperado ({type(error).__name__}): {error}")
        raise SystemExit(1)

    print(f"Embedding calculado: {len(vector)} dimensiones. Primeros valores: {vector[:3]}")
