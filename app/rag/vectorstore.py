import chromadb

from app.ingestion.md_chunker import Chunk
from app.rag.embeddings import embed_documents, embed_query

_client = chromadb.PersistentClient(path="data/chroma")
_collection = _client.get_or_create_collection(
    name="knowledge_base", metadata={"hnsw:space": "cosine"}
)


def chunk_to_embed_text(chunk: Chunk) -> str:
    return " > ".join(chunk.heading_path) + "\n" + chunk.text


def add_chunks(chunks: list[Chunk]) -> None:
    _collection.upsert(
        ids=[f"{c.doc_id}:{c.index}" for c in chunks],
        embeddings=embed_documents([chunk_to_embed_text(c) for c in chunks]),
        documents=[c.text for c in chunks],
        metadatas=[
            {"doc_id": c.doc_id, "heading": " > ".join(c.heading_path)}
            for c in chunks
        ],
    )


def delete_document(doc_id: str) -> None:
    _collection.delete(where={"doc_id": doc_id})


def reindex_document(doc_id: str, chunks: list[Chunk]) -> None:
    delete_document(doc_id)
    add_chunks(chunks)


def search(query: str, k: int = 3) -> list[dict]:
    res = _collection.query(query_embeddings=[embed_query(query)], n_results=k)
    return [
        {
            "text": t,
            "heading": m["heading"],
            "doc_id": m["doc_id"],
            "distance": d,
        }
        for t, m, d in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0]
        )
    ]
