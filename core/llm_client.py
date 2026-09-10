"""Provider-agnostic streaming LLM client.

One interface, two providers (Anthropic / OpenAI), selected by environment variables so
behavior is identical and providers are swappable (Constitution Principle II, FR-013).
SDKs are imported lazily so unit tests and non-LLM code don't require them installed.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

# Conversation history / messages are simple dicts: {"role": "user"|"assistant", "content": str}
Message = dict[str, str]

# Per-provider default models; override with the LLM_MODEL env var.
_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-5",
    "openai": "gpt-4o-mini",
}
_MAX_TOKENS = 1024


class LLMError(Exception):
    """Raised when the provider call fails. Never carries secrets or stack traces."""


class LLMClient:
    """Reads provider + key from the environment and streams completions."""

    def __init__(self) -> None:
        self.provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
        self.api_key = os.environ.get("LLM_API_KEY", "").strip()
        self.model = os.environ.get("LLM_MODEL", "").strip() or _DEFAULT_MODELS.get(self.provider)

        if self.provider not in _DEFAULT_MODELS:
            raise LLMError(
                "LLM_PROVIDER must be 'anthropic' or 'openai' "
                f"(got: {self.provider!r}). Set it in your environment or .env."
            )
        if not self.api_key:
            raise LLMError("LLM_API_KEY is not set. Provide it via environment or .env.")

    def stream(self, system: str, history: list[Message], message: str) -> Iterator[str]:
        """Yield response text chunks for the given system prompt, history, and new message."""
        messages = [*history, {"role": "user", "content": message}]
        try:
            if self.provider == "anthropic":
                yield from self._stream_anthropic(system, messages)
            else:
                yield from self._stream_openai(system, messages)
        except LLMError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalize any provider error, drop details
            raise LLMError(f"LLM provider request failed: {type(exc).__name__}") from None

    def _stream_anthropic(self, system: str, messages: list[Message]) -> Iterator[str]:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        with client.messages.stream(
            model=self.model,
            max_tokens=_MAX_TOKENS,
            system=system,
            messages=messages,
        ) as stream:
            yield from stream.text_stream

    def _stream_openai(self, system: str, messages: list[Message]) -> Iterator[str]:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, *messages],
            max_tokens=_MAX_TOKENS,
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
