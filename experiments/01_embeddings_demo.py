import numpy as np
import ollama

MODEL = "nomic-embed-text"

def embed(text: str, kind: str) -> np.ndarray:
    response = ollama.embed(model=MODEL, input=f"{kind}: {text}")
    return np.array(response["embeddings"][0])


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


v = embed("Where is the bank for me to save money?", "search_query")
print("shape:", v.shape)
print("first 5 numbers:", v[:5])
print("length (L2 norm):", np.linalg.norm(v))

query = embed("Where is the bank for me to save money?", "search_query")
candidates = [
    "river bank is located on the corner of 5th and Main",
    "financial bank is open from 9am to 5pm",
    "Open a savings account at our branch to deposit money",
]
for text in candidates:
    print(f"{cosine(query, embed(text, 'search_document')):.3f}  {text}")
