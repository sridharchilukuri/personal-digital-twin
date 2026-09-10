import pytest

from core.llm_client import LLMClient, LLMError


def test_missing_provider_raises(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("LLM_API_KEY", "k")
    with pytest.raises(LLMError):
        LLMClient()


def test_bad_provider_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "notreal")
    monkeypatch.setenv("LLM_API_KEY", "k")
    with pytest.raises(LLMError):
        LLMClient()


def test_missing_key_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(LLMError):
        LLMClient()


def test_provider_and_default_model_selected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "k")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    client = LLMClient()
    assert client.provider == "openai"
    assert client.model  # a default was chosen


def test_stream_dispatches_to_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_API_KEY", "k")
    client = LLMClient()

    monkeypatch.setattr(client, "_stream_anthropic", lambda system, messages: iter(["Hi", " there"]))
    out = list(client.stream("system", [], "hello"))
    assert out == ["Hi", " there"]


def test_stream_wraps_provider_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_API_KEY", "k")
    client = LLMClient()

    def boom(system, messages):
        raise RuntimeError("network exploded with secret sk-123")
        yield  # pragma: no cover

    monkeypatch.setattr(client, "_stream_anthropic", boom)
    with pytest.raises(LLMError) as exc:
        list(client.stream("system", [], "hello"))
    # error is normalized and does not leak the underlying message/secret
    assert "sk-123" not in str(exc.value)
