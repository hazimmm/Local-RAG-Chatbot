import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api import routes_admin, routes_auth
from app.db import Base, engine
from app.rag.generator import answer_stream

app = FastAPI(title="Local RAG Chatbot")
Base.metadata.create_all(engine)
app.include_router(routes_auth.router)
app.include_router(routes_admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/fake-stream")
async def fake_stream(text: str = "hello from a streaming server"):
    async def event_generator():
        for word in text.split():
            payload = json.dumps({"token": word + " "})
            yield f"data: {payload}\n\n"
            await asyncio.sleep(0.3)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


class ChatRequest(BaseModel):
    question: str
    k: int = 4


def sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@app.post("/chat")
def chat(req: ChatRequest):
    sources, tokens = answer_stream(req.question, k=req.k)

    def events():
        yield sse({"type": "sources", "sources": sources})
        for t in tokens:
            yield sse({"type": "token", "token": t})
        yield "data: [DONE]\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
