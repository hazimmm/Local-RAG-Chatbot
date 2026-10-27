"""Re-grade saved answers with the automated checks (no regeneration)."""
import json
from pathlib import Path

from app.rag.retriever import retrieve
from eval.faithfulness import check_numbers, check_quotes

SRC = Path("eval/results/gen_baseline.json")
OUT = Path("eval/results/gen_regraded.json")

data = json.loads(SRC.read_text(encoding="utf-8"))
for row in data["rows"]:
    if row["refused"]:
        continue
    results = retrieve(row["question"], None, 4)
    context = "\n\n".join(r["text"] for r in results)
    ok_n, missing = check_numbers(row["answer"], context, row["question"])
    ok_q, bad = check_quotes(row["answer"], context)
    row["faithful_llm3b"] = row["faithful"]
    row["faithful_numbers"], row["numbers_missing"] = ok_n, missing
    row["faithful_quotes"], row["quotes_unverified"] = ok_q, bad
    print(row["id"], "numbers", ok_n, missing, "| quotes", ok_q, flush=True)

OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False),
               encoding="utf-8")
