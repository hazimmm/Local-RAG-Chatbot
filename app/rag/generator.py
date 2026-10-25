from collections.abc import Iterator

import ollama

from app.rag.prompt import build_messages
from app.rag.vectorstore import search

CHAT_MODEL = "llama3.2:3b"


def answer_stream(question: str, k: int = 4) -> tuple[list[dict], Iterator[str]]:
    results = search(question, k=k)
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
