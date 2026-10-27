"""Compare a results file's automated faithfulness verdicts with labels."""
import json
import sys
from pathlib import Path

results = Path(sys.argv[1] if len(sys.argv) > 1
               else "eval/results/gen_baseline.json")
field = sys.argv[2] if len(sys.argv) > 2 else "faithful"
rows = {r["id"]: r for r in json.loads(results.read_text(encoding="utf-8"))["rows"]}
labels = json.loads(Path("eval/human_labels.json").read_text(encoding="utf-8"))["labels"]

agree = tp = tn = fp = fn = 0
for lab in labels:
    row = rows.get(lab["id"])
    if row is None or field not in row:
        continue
    auto, truth = row[field], lab["faithful"]
    agree += auto == truth
    tp += (not auto) and (not truth)   # correctly flagged unfaithful
    tn += auto and truth               # correctly passed
    fp += (not auto) and truth         # false alarm
    fn += auto and (not truth)         # missed a bad answer
n = tp + tn + fp + fn
print(f"agreement {agree}/{n} = {agree / n:.0%}")
print(f"caught unfaithful: {tp}/{tp + fn}   false alarms: {fp}/{fp + tn}")
