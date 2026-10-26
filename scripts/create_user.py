import getpass
import sys

from app import models
from app.auth import hash_password
from app.db import Base, SessionLocal, engine

username = sys.argv[1]
role = sys.argv[2] if len(sys.argv) > 2 else "user"
password = getpass.getpass(f"Password for {username}: ")

Base.metadata.create_all(engine)
with SessionLocal() as db:
    db.add(models.User(
        username=username, password_hash=hash_password(password), role=role
    ))
    db.commit()
print(f"Created {role} '{username}'")
