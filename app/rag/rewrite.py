import ollama

from app.rag.generator import CHAT_MODEL

REWRITE_SYSTEM = """You rewrite a user's latest question so that it can be \
understood without the conversation.
Rules:
- Only use the earlier USER questions to resolve vague words such as it, \
that, they, "and for X?".
- Keep all names, numbers and key terms from the latest question.
- If the latest question already makes sense on its own, or is about a \
different topic, return it EXACTLY unchanged.
- Never answer the question. Never add facts.
- Output only the question.

Example 1
Earlier user questions:
- How many days of annual leave do I get?
Latest question: And for sick leave?
Rewritten: How many days of sick leave do I get?

Example 2
Earlier user questions:
- How do I reset my password?
Latest question: What are the branch opening hours?
Rewritten: What are the branch opening hours?"""

HISTORY_USER_QUESTIONS = 3


def user_questions(history: list[dict]) -> list[str]:
    asked = [m["content"] for m in history if m["role"] == "user"]
    return asked[-HISTORY_USER_QUESTIONS:]


def rewrite_question(history: list[dict], question: str) -> str:
    asked = user_questions(history)
    if not asked:
        return question
    bullets = "\n".join(f"- {q}" for q in asked)
    prompt = (
        f"Earlier user questions:\n{bullets}\n"
        f"Latest question: {question}\nRewritten:"
    )
    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": REWRITE_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0},
    )
    lines = response["message"]["content"].strip().splitlines()
    rewritten = lines[0].strip().strip('"') if lines else ""
    if rewritten.lower().startswith("rewritten:"):
        rewritten = rewritten[len("rewritten:"):].strip()
    if not rewritten or len(rewritten) > 300:
        return question
    return rewritten
