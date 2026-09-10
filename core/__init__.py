"""The UI-agnostic agent core. Imports no UI framework (Constitution Principle II).

Public surface (see specs/001-grounded-twin/contracts/core-interface.md):
    load_corpus, build_system_prompt, LLMClient, LLMError, Message, answer
"""

from __future__ import annotations

from collections.abc import Iterator

from core.corpus_loader import load_corpus
from core.llm_client import LLMClient, LLMError, Message
from core.prompt import REFUSAL_MARKER, SCOPE_MARKER, build_system_prompt

__all__ = [
    "load_corpus",
    "build_system_prompt",
    "LLMClient",
    "LLMError",
    "Message",
    "REFUSAL_MARKER",
    "SCOPE_MARKER",
    "answer",
]

_EMPTY_INPUT_REPLY = (
    "Ask me anything about Sridhar — his experience, projects, skills, or interests."
)

# The system prompt (persona + guardrail + corpus) is stable, so build it once and reuse.
_system_prompt: str | None = None


def _get_system_prompt() -> str:
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = build_system_prompt(load_corpus())
    return _system_prompt


def answer(message: str, history: list[Message] | None = None) -> Iterator[str]:
    """Stream a grounded reply to ``message`` given prior ``history``.

    Empty/whitespace input yields a prompt-for-a-question reply without calling the model.
    """
    if not message or not message.strip():
        yield _EMPTY_INPUT_REPLY
        return

    client = LLMClient()
    yield from client.stream(_get_system_prompt(), history or [], message)
