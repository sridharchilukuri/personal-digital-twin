"""FastAPI web app — a thin shell over core/ (Constitution Principle II).

Serves the static site (web/) and a streaming /api/chat endpoint that calls core.answer().
Knows nothing about prompts or providers.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core import LLMError, Message, answer

load_dotenv()  # local dev reads .env; in prod the host injects env from Secret Manager

WEB_DIR = Path(__file__).parent / "web"

app = FastAPI(title="Sridhar's Digital Twin")


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
def chat(req: ChatRequest) -> StreamingResponse:
    """Stream the twin's grounded reply as plain-text chunks."""

    def generate():
        try:
            yield from answer(req.message, req.history)
        except LLMError:
            yield "\n\n_(Sorry — I'm having trouble reaching my brain right now. Please try again in a moment.)_"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


# Serve the static site. Mounted last so API routes above take precedence.
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
