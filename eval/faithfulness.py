"""Two automated faithfulness checks, validated against eval/human_labels.json."""
import json
import re

import ollama

from app.rag.generator import CHAT_MODEL

CITATION = re.compile(r"\[\d+\]")
NUMBER = re.compile(r"\d[\d,.:]*\w*")


def normalize(text: str) -> str:
    text = CITATION.sub(" ", text.lower())
    text = re.sub(r"[*_`]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def ungrounded_numbers(answer: str, context: str, question: str = "") -> list[str]:
    """Numbers in the answer (e.g. 2,000 / 7:30am / 4th) absent from context.

    Numbers the user typed in the question may be echoed back, so they count
    as grounded.
    """
    ctx = normalize(context + " " + question)
    found = [n.rstrip(".,:") for n in NUMBER.findall(normalize(answer))]
    return [n for n in found if n and n not in ctx]


def check_numbers(answer: str, context: str,
                  question: str = "") -> tuple[bool, list[str]]:
    missing = ungrounded_numbers(answer, context, question)
    return (not missing, missing)


QUOTE_SYSTEM = (
    "You are a fact checker. You get a CONTEXT and an ANSWER. Split the "
    "ANSWER into its factual claims. For each claim, copy ONE sentence or "
    "phrase from the CONTEXT, word for word, that proves it. If nothing in "
    "the CONTEXT proves a claim, use null as the quote.\n"
    'Reply with JSON only: {"claims": [{"claim": "...", "quote": "..."}]}'
)


def check_quotes(answer: str, context: str) -> tuple[bool, list[str]]:
    """Faithful only if every claim has a quote that really is in the context."""
    out = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": QUOTE_SYSTEM},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\n"
                                        f"ANSWER:\n{answer}"},
        ],
        format="json",
        options={"temperature": 0},
    )
    try:
        claims = json.loads(out["message"]["content"])["claims"]
    except (ValueError, KeyError, TypeError):
        return False, ["unparseable judge output"]
    if not claims:
        return False, ["no claims returned"]
    ctx = normalize(context)
    bad = []
    for c in claims:
        quote = c.get("quote") if isinstance(c, dict) else None
        if not quote or normalize(str(quote)) not in ctx:
            bad.append(str(c.get("claim") if isinstance(c, dict) else c)[:80])
    return (not bad, bad)
