from app.ingestion.md_chunker import chunk_markdown
from app.ingestion.to_markdown import to_markdown
from app.rag.vectorstore import add_chunks, search

md = to_markdown("samples/handbook.docx")
add_chunks(chunk_markdown(md, "handbook"))

for q in ["How do I reset my password?", "When can I visit the branch?",
          "How many vacation days do I get?"]:
    print("\nQ:", q)
    for r in search(q, k=2):
        print(f"  {r['distance']:.3f}  [{r['heading']}]")
