import sys

from app.rag.generator import answer_stream

question = " ".join(sys.argv[1:]) or "How do I reset my password?"
sources, tokens = answer_stream(question)

print("Q:", question, "\nA: ", end="", flush=True)
for t in tokens:
    print(t, end="", flush=True)

print("\n\nSources:")
for i, s in enumerate(sources, start=1):
    print(f"  [{i}] {s['heading']} (distance {s['distance']:.3f})")
