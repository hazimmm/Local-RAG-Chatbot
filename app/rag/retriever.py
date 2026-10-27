from app.rag.vectorstore import search


def retrieve(question: str, rewritten: str | None = None, k: int = 4) -> list[dict]:
    """Search with the original and the rewritten question, keep best k."""
    queries = [question]
    if rewritten and rewritten.strip().lower() != question.strip().lower():
        queries.append(rewritten)
    best: dict[tuple, dict] = {}
    for q in queries:
        for r in search(q, k):
            key = (r["doc_id"], r["heading"], r["text"])
            if key not in best or r["distance"] < best[key]["distance"]:
                best[key] = r
    return sorted(best.values(), key=lambda r: r["distance"])[:k]
