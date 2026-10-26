from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import create_token, get_current_user, verify_password
from app.db import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=req.username).first()
    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Wrong username or password")
    return {"access_token": create_token(user), "role": user.role}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "role": user.role}
