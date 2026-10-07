"""FastAPI web app — a thin shell over core/ (Constitution Principle II).

Serves the static site (web/) and a streaming /api/chat endpoint that calls core.answer().
Knows nothing about prompts or providers.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core import REFUSAL_MARKER, LLMError, answer

load_dotenv()  # local dev reads .env; in prod the host injects env from Secret Manager

WEB_DIR = Path(__file__).parent / "web"

# Cheap cost/abuse guardrails: bound what a single request can send to the model.
MAX_MESSAGE_CHARS = 500
MAX_TURN_CHARS = 2000
MAX_HISTORY_TURNS = 10

logger = logging.getLogger("twin")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Sridhar's Digital Twin")


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=MAX_TURN_CHARS)


class ChatRequest(BaseModel):
    message: str = Field(max_length=MAX_MESSAGE_CHARS)
    history: list[ChatTurn] = Field(default_factory=list, max_length=MAX_HISTORY_TURNS)


# Cloud Run's front end reserves /healthz on *.run.app (it 404s before reaching the app),
# so the web UI's status badge uses /api/health. /healthz stays for local and other hosts.
@app.get("/api/health")
@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
def chat(req: ChatRequest) -> StreamingResponse:
    """Stream the twin's grounded reply as plain-text chunks."""
    history = [turn.model_dump() for turn in req.history]

    def generate():
        reply: list[str] = []
        try:
            for chunk in answer(req.message, history):
                reply.append(chunk)
                yield chunk
        except LLMError:
            yield "\n\n_(Sorry — I'm having trouble reaching my brain right now. Please try again in a moment.)_"
            return
        # Corpus-gap signal: questions the twin couldn't answer show up in the host's logs.
        if REFUSAL_MARKER.lower() in "".join(reply).lower():
            logger.info("unanswered question: %r", req.message)

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


# Serve the static site. Mounted last so API routes above take precedence.
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
