SYSTEM_PROMPT = """You are a helpful assistant that answers questions using \
only the provided context.
Rules:
- Use only facts found in the context. Do not use outside knowledge.
- If the context does not contain the answer, reply exactly: \
"I don't know based on the provided documents."
- Cite the sources you used as [1], [2] after the relevant sentence.
- Be concise."""


def build_context(results: list[dict]) -> str:
    blocks = []
    for i, r in enumerate(results, start=1):
        blocks.append(f"[{i}] ({r['heading']})\n{r['text']}")
    return "\n\n".join(blocks)


def build_messages(question: str, results: list[dict]) -> list[dict]:
    user = f"Context:\n{build_context(results)}\n\nQuestion: {question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
