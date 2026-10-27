"""Upload every file in a folder through the real admin API (in-process).

Usage: python -m scripts.ingest_dir samples/distractors
"""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import app
from app.auth import create_token
from app.db import SessionLocal
from app.models import User

folder = Path(sys.argv[1])
with SessionLocal() as db:
    admin = db.query(User).filter_by(role="admin").first()
    headers = {"Authorization": f"Bearer {create_token(admin)}"}

client = TestClient(app)
for path in sorted(folder.iterdir()):
    with path.open("rb") as f:
        resp = client.post("/admin/documents", headers=headers,
                           files={"file": (path.name, f)})
    body = resp.json()
    doc = body["document"]
    print(f"{path.name}: {body['result']} -> {doc['status']}, "
          f"{doc['chunk_count']} chunks")
