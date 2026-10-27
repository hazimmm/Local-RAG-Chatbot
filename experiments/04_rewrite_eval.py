import ollama

from app.rag.generator import CHAT_MODEL
from app.rag.rewrite import rewrite_question as rewrite_v2
from app.rag.vectorstore import search

V1_SYSTEM = (
    "You rewrite a user's latest question so it can be understood without "
    "the conversation. Replace pronouns and vague references with what they "
    "refer to. Keep names and numbers. Do NOT answer. If already clear, "
    "return it unchanged. Output only the question."
)


def rewrite_v1(history, question):
    if not history:
        return question
    convo = "\n".join(
        f"{m['role'].capitalize()}: {m['content'][:500]}" for m in history[-4:]
    )
    out = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": V1_SYSTEM},
            {"role": "user", "content": f"Conversation:\n{convo}\n\n"
                                        f"Latest question: {question}\n\n"
                                        "Rewritten question:"},
        ],
        options={"temperature": 0},
    )
    return out["message"]["content"].strip().splitlines()[0].strip('"')


def turn(q, a):
    return [{"role": "user", "content": q}, {"role": "assistant", "content": a}]


SICK = turn("how many days of sick leave do i get?", "You receive 10 days of paid sick leave per year. [1]")
PW = turn("how do i reset my password?", "To reset your password, open the IT portal and choose Reset Credentials.")
MEAL = turn("what is the daily meal allowance?", "The daily meal allowance during business travel is 60 dollars. [1]")
PARENT = turn("how long is parental leave?", "Primary caregivers receive 14 weeks of paid parental leave. [1]")
FEE = turn("what is the fee for a replacement card?", "A replacement card costs 10 dollars. [1]")

CASES = [
    ("follow-up", SICK, "do i need a certificate for it?", "sick leave"),
    ("follow-up", PW, "how often does it expire?", "assword"),
    ("follow-up", MEAL, "and for hotel?", "hotel"),
    ("follow-up", PARENT, "and for the secondary caregiver?", "parental"),
    ("follow-up", FEE, "and for a cheque book?", "service charges"),
    ("standalone", SICK, "what is the daily meal allowance?", "meals"),
    ("standalone", PW, "what are the branch opening hours?", "branch"),
    ("standalone", MEAL, "how do i report a phishing email?", "phishing"),
    ("standalone", PARENT, "what is the interest rate on savings accounts?", "interest"),
]


def hit(results, needle, n):
    return any(needle in r["heading"].lower() for r in results[:n])


def merged(q, rq, k=4):
    best = {}
    for r in search(q, k) + search(rq, k):
        key = (r["doc_id"], r["heading"], r["text"])
        if key not in best or r["distance"] < best[key]["distance"]:
            best[key] = r
    return sorted(best.values(), key=lambda r: r["distance"])[:k]


scores = {name: [0, 0] for name in ["none", "v1", "v2", "v2+merge"]}
for kind, hist, q, needle in CASES:
    r1, r2 = rewrite_v1(hist, q), rewrite_v2(hist, q)
    runs = {
        "none": search(q, 4),
        "v1": search(r1, 4),
        "v2": search(r2, 4),
        "v2+merge": merged(q, r2),
    }
    row = []
    for name, res in runs.items():
        scores[name][0] += hit(res, needle, 1)
        scores[name][1] += hit(res, needle, 4)
        row.append(f"{name}:{'Y' if hit(res, needle, 1) else '-'}/{'Y' if hit(res, needle, 4) else '-'}")
    print(f"[{kind:10}] {q}\n    v1 -> {r1}\n    v2 -> {r2}\n    top1/top4  " + "  ".join(row))

print("\nSummary over", len(CASES), "cases (top1 hits / top4 hits)")
for name, (a, b) in scores.items():
    print(f"  {name:9} {a}/{len(CASES)}   {b}/{len(CASES)}")
