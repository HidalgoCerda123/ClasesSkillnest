"""Reconecta con el vector store persistido, sin re-indexar (Bloque 24)."""

import sys

from langchain_chroma import Chroma

from indexar_corpus import DIRECTORIO_VECTORSTORE, crear_embeddings

if __name__ == "__main__":
    vectorstore = Chroma(
        persist_directory=DIRECTORIO_VECTORSTORE,
        embedding_function=crear_embeddings(),
    )
    cantidad = vectorstore._collection.count()
    print(f"Chunks en {DIRECTORIO_VECTORSTORE}: {cantidad}")
    if cantidad == 0:
        raise SystemExit("El vector store está vacío: ejecuta antes python indexar_corpus.py.")

    # Una consulta de ejemplo: solo calcula el embedding de la pregunta.
    pregunta = " ".join(sys.argv[1:]) or "¿Qué pasa si recibo un error 429?"
    print(f"\nPregunta: {pregunta}")
    for chunk in vectorstore.similarity_search(pregunta, k=2):
        print(f"- [{chunk.metadata['documento']}] {chunk.page_content}")
