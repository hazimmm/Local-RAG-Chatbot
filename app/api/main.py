import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from app.api import routes_admin, routes_auth, routes_chat
from app.db import Base, engine

app = FastAPI(title="Local RAG Chatbot")
Base.metadata.create_all(engine)
app.include_router(routes_auth.router)
app.include_router(routes_admin.router)
app.include_router(routes_chat.router)


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
