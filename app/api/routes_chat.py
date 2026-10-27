import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import SessionLocal, get_db
from app.models import ChatSession, Message, User
from app.rag.generator import answer_stream

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None
    k: int = 4


def sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def get_owned_session(db: Session, session_id: str, user: User) -> ChatSession:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(404, "Session not found")
    return session


def save_assistant_message(session_id: str, text: str, sources: list) -> None:
    with SessionLocal() as db:
        db.add(
            Message(
                session_id=session_id,
                role="assistant",
                content=text,
                sources=json.dumps(sources),
            )
        )
        db.commit()


@router.post("/chat")
def chat(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.session_id:
        session = get_owned_session(db, req.session_id, user)
    else:
        session = ChatSession(user_id=user.id, title=req.question[:60])
        db.add(session)
        db.commit()
    db.add(Message(session_id=session.id, role="user", content=req.question))
    db.commit()
    session_id = session.id

    sources, tokens = answer_stream(req.question, k=req.k)

    def events():
        parts: list[str] = []
        try:
            yield sse({"type": "meta", "session_id": session_id})
            yield sse({"type": "sources", "sources": sources})
            for t in tokens:
                parts.append(t)
                yield sse({"type": "token", "token": t})
            yield "data: [DONE]\n\n"
        finally:
            tokens.close()
            if parts:
                save_assistant_message(session_id, "".join(parts), sources)

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("/sessions")
def list_sessions(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    rows = (
        db.query(ChatSession)
        .filter_by(user_id=user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [
        {"id": s.id, "title": s.title, "created_at": s.created_at.isoformat()}
        for s in rows
    ]


@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_owned_session(db, session_id, user)
    return {
        "id": session.id,
        "title": session.title,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "sources": json.loads(m.sources) if m.sources else [],
            }
            for m in session.messages
        ],
    }
