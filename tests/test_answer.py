import core


def test_empty_input_returns_prompt_without_calling_model(monkeypatch):
    # If answer() tried to build the prompt or call the LLM, this would blow up.
    def explode():
        raise AssertionError("should not build prompt / call LLM for empty input")

    monkeypatch.setattr(core, "_get_system_prompt", explode)

    for message in ["", "   ", "\n\t "]:
        out = list(core.answer(message, []))
        assert len(out) == 1
        assert "Ask me anything" in out[0]


def test_answer_streams_from_client(monkeypatch):
    monkeypatch.setattr(core, "_get_system_prompt", lambda: "SYSTEM")

    class FakeClient:
        def stream(self, system, history, message):
            assert system == "SYSTEM"
            assert message == "hello"
            yield "grounded "
            yield "reply"

    monkeypatch.setattr(core, "LLMClient", FakeClient)

    out = list(core.answer("hello", []))
    assert "".join(out) == "grounded reply"
