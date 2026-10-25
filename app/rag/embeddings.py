import ollama

EMBED_MODEL = "nomic-embed-text"


def embed_documents(texts: list[str]) -> list[list[float]]:
    inputs = [f"search_document: {t}" for t in texts]
    return ollama.embed(model=EMBED_MODEL, input=inputs)["embeddings"]


def embed_query(text: str) -> list[float]:
    return ollama.embed(
        model=EMBED_MODEL, input=f"search_query: {text}"
    )["embeddings"][0]
