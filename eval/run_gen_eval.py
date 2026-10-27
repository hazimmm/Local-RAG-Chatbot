"""Generation evaluation: refusals, key-fact correctness, faithfulness."""
import argparse
import json
import time
from pathlib import Path

import ollama

from app.rag.generator import CHAT_MODEL
from app.rag.prompt import build_messages
from app.rag.retriever import retrieve

REFUSAL_PREFIX = "i don't know based on"
JUDGE_SYSTEM = (
    "You are a strict fact checker. You get a CONTEXT and an ANSWER. "
    "Reply with exactly one word. Reply SUPPORTED if every factual claim in "
    "the ANSWER is stated in the CONTEXT. Otherwise reply UNSUPPORTED."
)


def generate(question: str, k: int) -> tuple[str, list[dict]]:
    results = retrieve(question, None, k)
    out = ollama.chat(
        model=CHAT_MODEL,
        messages=build_messages(question, results),
        options={"temperature": 0.1},
    )
    return out["message"]["content"].strip(), results


def judge_faithful(answer: str, results: list[dict]) -> tuple[bool, str]:
    context = "\n\n".join(r["text"] for r in results)
    out = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\n"
                                        f"ANSWER:\n{answer}"},
        ],
        options={"temperature": 0},
    )
    verdict = out["message"]["content"].strip().upper()
    return (verdict.startswith("SUPPORTED"), verdict[:40])


def has_all_facts(answer: str, facts: list[str]) -> bool:
    text = answer.lower()
    return all(any(alt in text for alt in f.lower().split("|")) for f in facts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", default="eval/results/gen_baseline.json")
    args = parser.parse_args()

    qa = json.loads(Path("eval/qa_set.json").read_text(encoding="utf-8"))
    if args.limit:
        qa = qa[: args.limit]
    rows = []
    for i, item in enumerate(qa, start=1):
        t0 = time.time()
        answer, results = generate(item["question"], args.k)
        refused = answer.lower().startswith(REFUSAL_PREFIX)
        row = {
            "id": item["id"], "type": item["type"],
            "answerable": item["answerable"], "question": item["question"],
            "answer": answer, "refused": refused,
            "retrieved": [r["heading"].split(" > ")[-1] for r in results],
        }
        if item["answerable"]:
            row["facts_ok"] = (not refused) and has_all_facts(
                answer, item["key_facts"])
        if not refused:
            row["faithful"], row["verdict"] = judge_faithful(answer, results)
        rows.append(row)
        print(f"[{i}/{len(qa)}] {item['id']} {time.time() - t0:.0f}s "
              f"refused={refused}", flush=True)

    ans = [r for r in rows if r["answerable"]]
    una = [r for r in rows if not r["answerable"]]
    graded = [r for r in rows if "faithful" in r]
    summary = {
        "answerable_n": len(ans),
        "correct (not refused + key facts)": sum(r["facts_ok"] for r in ans),
        "false_refusals": sum(r["refused"] for r in ans),
        "unanswerable_n": len(una),
        "correct_refusals": sum(r["refused"] for r in una),
        "faithful_of_non_refused": f"{sum(r['faithful'] for r in graded)}/"
                                   f"{len(graded)}",
    }
    print("\n" + json.dumps(summary, indent=2))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(
        json.dumps({"summary": summary, "rows": rows}, indent=2,
                   ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
