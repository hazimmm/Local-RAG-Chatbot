import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.config import KB_DIR, MIN_MARKDOWN_CHARS, RAW_DIR
from app.db import get_db
from app.ingestion.md_chunker import chunk_markdown
from app.ingestion.to_markdown import to_markdown
from app.models import Document
from app.rag.vectorstore import delete_document, reindex_document

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


def doc_to_dict(doc: Document) -> dict:
    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        "error": doc.error,
        "chunk_count": doc.chunk_count,
        "uploaded_at": doc.uploaded_at.isoformat(),
    }


def remove_files(doc_id: str) -> None:
    for path in RAW_DIR.glob(f"{doc_id}.*"):
        path.unlink()
    (KB_DIR / f"{doc_id}.md").unlink(missing_ok=True)


@router.post("/documents")
def upload_document(file: UploadFile, db: Session = Depends(get_db)):
    data = file.file.read()
    filename = Path(file.filename or "unnamed").name
    digest = hashlib.sha256(data).hexdigest()

    same_content = db.query(Document).filter_by(content_hash=digest).first()
    if same_content is not None and same_content.status == "ready":
        return {"result": "duplicate", "document": doc_to_dict(same_content)}

    doc = db.query(Document).filter_by(filename=filename).first()
    result = "replaced" if doc else "created"
    if doc is None:
        doc = Document(filename=filename)
        db.add(doc)
    doc.content_hash = digest
    doc.status = "processing"
    doc.error = None
    db.commit()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    KB_DIR.mkdir(parents=True, exist_ok=True)
    remove_files(doc.id)
    raw_path = RAW_DIR / f"{doc.id}{Path(filename).suffix.lower()}"
    raw_path.write_bytes(data)

    try:
        markdown = to_markdown(raw_path)
        if len(markdown.strip()) < MIN_MARKDOWN_CHARS:
            raise ValueError("No extractable text (scanned document?)")
        (KB_DIR / f"{doc.id}.md").write_text(markdown, encoding="utf-8")
        chunks = chunk_markdown(markdown, doc.id)
        reindex_document(doc.id, chunks)
        doc.status = "ready"
        doc.chunk_count = len(chunks)
    except Exception as exc:
        doc.status = "failed"
        doc.error = str(exc)
    db.commit()
    return {"result": result, "document": doc_to_dict(doc)}


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return [doc_to_dict(d) for d in docs]


@router.delete("/documents/{doc_id}")
def delete_doc(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    delete_document(doc_id)
    remove_files(doc_id)
    db.delete(doc)
    db.commit()
    return {"deleted": doc_id}
