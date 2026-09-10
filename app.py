"""Gradio chat UI — a thin shell over core/ (Constitution Principle II).

This file knows nothing about prompts or providers; it just streams core.answer() into a
chat window. It's disposable: the valuable logic lives in core/.
"""

from __future__ import annotations

import os

import gradio as gr
from dotenv import load_dotenv

from core import LLMError, answer

load_dotenv()  # load .env for local dev; in prod, env comes from the host / Secret Manager

_ERROR_REPLY = (
    "Sorry — I'm having trouble reaching my brain right now. Please try again in a moment."
)


def respond(message, history):
    """Stream the twin's reply, accumulating chunks for Gradio's streaming display."""
    try:
        accumulated = ""
        for chunk in answer(message, history):
            accumulated += chunk
            yield accumulated
    except LLMError:
        yield _ERROR_REPLY


demo = gr.ChatInterface(
    respond,
    type="messages",
    title="Ask Sridhar's Twin",
    description=(
        "A grounded AI twin of Sridhar Chilukuri. It answers only from what Sridhar has "
        "shared, and it will tell you when it doesn't know."
    ),
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 8080)))
