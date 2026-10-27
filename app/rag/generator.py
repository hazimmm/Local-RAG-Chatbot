from collections.abc import Iterator

import ollama

from app.rag.prompt import build_messages
from app.rag.retriever import retrieve

CHAT_MODEL = "llama3.2:3b"


def answer_stream(
    question: str, k: int = 4, search_question: str | None = None
) -> tuple[list[dict], Iterator[str]]:
    results = retrieve(question, search_question, k)
    messages = build_messages(question, results)

    def tokens() -> Iterator[str]:
        stream = ollama.chat(
            model=CHAT_MODEL,
            messages=messages,
            stream=True,
            options={"temperature": 0.1},
        )
        for part in stream:
            yield part["message"]["content"]

    return results, tokens()
