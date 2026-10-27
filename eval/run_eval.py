"""Retrieval evaluation: hit-rate@k, MRR and recall@k on the golden set."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from app.db import SessionLocal
from app.models import Document
from app.rag.vectorstore import search

KS = (1, 3, 5)


def load_doc_names() -> dict[str, str]:
    with SessionLocal() as db:
        return {d.id: d.filename for d in db.query(Document).all()}


def is_relevant(result: dict, relevant: list[dict], names: dict) -> bool:
    doc = names.get(result["doc_id"])
    return any(
        doc == rel["doc"] and rel["heading"].lower() in result["heading"].lower()
        for rel in relevant
    )


def first_relevant_rank(results, relevant, names):
    for rank, r in enumerate(results, start=1):
        if is_relevant(r, relevant, names):
            return rank
    return None


def recall_at_k(results, relevant, names, k):
    found = {
        (rel["doc"], rel["heading"])
        for rel in relevant
        for r in results[:k]
        if names.get(r["doc_id"]) == rel["doc"]
        and rel["heading"].lower() in r["heading"].lower()
    }
    return len(found) / len(relevant)


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    out = {"n": n}
    for k in KS:
        out[f"hit@{k}"] = sum(r["rank"] is not None and r["rank"] <= k
                              for r in rows) / n
        out[f"recall@{k}"] = sum(r[f"recall@{k}"] for r in rows) / n
    out["mrr"] = sum(1 / r["rank"] for r in rows if r["rank"]) / n
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--out", default=None, help="save JSON results here")
    args = parser.parse_args()

    names = load_doc_names()
    qa = json.loads(Path("eval/qa_set.json").read_text(encoding="utf-8"))
    rows, unanswerable_dist = [], []
    for item in qa:
        results = search(item["question"], k=args.k)
        if not item["answerable"]:
            unanswerable_dist.append(results[0]["distance"])
            continue
        rows.append({
            "id": item["id"], "type": item["type"],
            "question": item["question"],
            "rank": first_relevant_rank(results, item["relevant"], names),
            "top_dist": results[0]["distance"],
            "got": [f"{names.get(r['doc_id'], '?')} | {r['heading'].split(' > ')[-1]}"
                    for r in results[:3]],
            **{f"recall@{k}": recall_at_k(results, item["relevant"], names, k)
               for k in KS},
        })

    overall = summarize(rows)
    print(f"Overall ({overall['n']} answerable questions)")
    print("  " + "  ".join(f"hit@{k}={overall[f'hit@{k}']:.2f}" for k in KS)
          + f"  MRR={overall['mrr']:.3f}  "
          + "  ".join(f"recall@{k}={overall[f'recall@{k}']:.2f}" for k in KS))

    by_type = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r)
    print("\nBy type            n   hit@1  hit@3  hit@5   MRR")
    for t, rs in sorted(by_type.items(), key=lambda kv: summarize(kv[1])["mrr"]):
        s = summarize(rs)
        print(f"  {t:14} {s['n']:3}   {s['hit@1']:.2f}   {s['hit@3']:.2f}   "
              f"{s['hit@5']:.2f}   {s['mrr']:.2f}")

    misses = [r for r in rows if r["rank"] != 1]
    print(f"\nNot ranked first ({len(misses)}):")
    for r in misses:
        print(f"  {r['id']} [{r['type']}] rank={r['rank']}  {r['question']}")
        for g in r["got"]:
            print(f"        got: {g}")

    ans_d = sum(r["top_dist"] for r in rows) / len(rows)
    una_d = sum(unanswerable_dist) / len(unanswerable_dist)
    print(f"\nMean top-1 distance: answerable={ans_d:.3f}  "
          f"unanswerable={una_d:.3f}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps({"overall": overall, "rows": rows}, indent=2),
            encoding="utf-8")


if __name__ == "__main__":
    main()
