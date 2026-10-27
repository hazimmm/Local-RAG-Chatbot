import os
from pathlib import Path

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 8

RAW_DIR = Path("data/raw")
KB_DIR = Path("data/kb")
MIN_MARKDOWN_CHARS = 50
