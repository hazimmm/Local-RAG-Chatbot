"""Check the golden set against the real converted documents."""
import json
from pathlib import Path

from app.ingestion.md_chunker import chunk_markdown
from app.ingestion.to_markdown import to_markdown

CORPUS = {p.name: p for p in Path("samples/corpus").iterdir()}
CORPUS["handbook.docx"] = Path("samples/handbook.docx")

markdown = {name: to_markdown(path) for name, path in CORPUS.items()}
chunks = {name: chunk_markdown(md, name) for name, md in markdown.items()}

problems = 0
for item in json.loads(Path("eval/qa_set.json").read_text(encoding="utf-8")):
    for rel in item["relevant"]:
        pool = chunks[rel["doc"]]
        matched = [c for c in pool
                   if rel["heading"].lower() in " > ".join(c.heading_path).lower()]
        if not matched:
            print(f"{item['id']}: no chunk in {rel['doc']} matches heading "
                  f"{rel['heading']!r}")
            problems += 1
    docs_text = " ".join(markdown[r["doc"]].lower() for r in item["relevant"])
    for fact in item["key_facts"]:
        if not any(alt in docs_text for alt in fact.lower().split("|")):
            print(f"{item['id']}: key fact {fact!r} not found in source docs")
            problems += 1
print("problems:", problems)
