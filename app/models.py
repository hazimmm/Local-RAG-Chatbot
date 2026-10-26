import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def new_id() -> str:
    return uuid.uuid4().hex


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="user")  # admin | user

    sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    filename: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="processing")
    error: Mapped[str | None] = mapped_column(Text, default=None)
    chunk_count: Mapped[int] = mapped_column(default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String, default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    user: Mapped[User] = relationship(back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="session", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id"))
    role: Mapped[str] = mapped_column(String)  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    sources: Mapped[str | None] = mapped_column(Text, default=None)  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    session: Mapped[ChatSession] = relationship(back_populates="messages")
