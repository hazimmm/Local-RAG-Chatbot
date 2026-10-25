import re
from dataclasses import dataclass

from tokenizers import Tokenizer

_tokenizer = Tokenizer.from_pretrained("nomic-ai/nomic-embed-text-v1.5")

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class Chunk:
    doc_id: str
    index: int
    heading_path: list[str]
    text: str


def count_tokens(text: str) -> int:
    return len(_tokenizer.encode(text, add_special_tokens=False).ids)


def split_sections(markdown: str) -> list[tuple[list[str], str]]:
    """Split markdown at headings. Returns (heading_path, body) per section."""
    sections = []
    path: list[str] = []
    body: list[str] = []

    def flush():
        text = "\n".join(body).strip()
        if text:
            sections.append((list(path), text))
        body.clear()

    for line in markdown.splitlines():
        m = HEADING_RE.match(line)
        if m:
            flush()
            level = len(m.group(1))
            path = path[: level - 1] + [m.group(2).strip()]
        else:
            body.append(line)
    flush()
    return sections


def split_by_tokens(text: str, max_tokens: int, overlap: int) -> list[str]:
    """Fallback for one paragraph longer than max_tokens: slide a token window."""
    enc = _tokenizer.encode(text, add_special_tokens=False)
    pieces = []
    step = max_tokens - overlap
    for start in range(0, len(enc.ids), step):
        window = enc.offsets[start : start + max_tokens]
        pieces.append(text[window[0][0] : window[-1][1]])
        if start + max_tokens >= len(enc.ids):
            break
    return pieces


def split_long_body(body: str, max_tokens: int, overlap: int) -> list[str]:
    """Pack paragraphs into pieces of at most max_tokens, carrying overlap forward."""
    if count_tokens(body) <= max_tokens:
        return [body]

    pieces: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for para in re.split(r"\n\s*\n", body):
        para_tokens = count_tokens(para)
        if para_tokens > max_tokens:
            if current:
                pieces.append("\n\n".join(current))
                current, current_tokens = [], 0
            pieces.extend(split_by_tokens(para, max_tokens, overlap))
            continue
        if current_tokens + para_tokens > max_tokens:
            pieces.append("\n\n".join(current))
            tail = current[-1]
            if count_tokens(tail) <= overlap:
                current, current_tokens = [tail], count_tokens(tail)
            else:
                current, current_tokens = [], 0
        current.append(para)
        current_tokens += para_tokens

    if current:
        pieces.append("\n\n".join(current))
    return pieces


def chunk_markdown(
    markdown: str, doc_id: str, max_tokens: int = 500, overlap: int = 50
) -> list[Chunk]:
    chunks = []
    for path, body in split_sections(markdown):
        for piece in split_long_body(body, max_tokens, overlap):
            chunks.append(Chunk(doc_id, len(chunks), path, piece))
    return chunks


if __name__ == "__main__":
    from app.ingestion.to_markdown import to_markdown

    md = to_markdown("samples/handbook.docx")
    for c in chunk_markdown(md, "handbook"):
        print(c.index, " > ".join(c.heading_path), f"({count_tokens(c.text)} tokens)")
        print(c.text, "\n---")
