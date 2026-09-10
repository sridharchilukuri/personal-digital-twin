from core.prompt import REFUSAL_MARKER, build_system_prompt


def test_prompt_includes_corpus_and_persona():
    prompt = build_system_prompt("SOME_CORPUS_TEXT")

    assert "SOME_CORPUS_TEXT" in prompt          # the corpus is stuffed in
    assert "first person" in prompt.lower()      # persona instruction present
    assert REFUSAL_MARKER in prompt              # honesty guardrail present
    assert "only" in prompt.lower()              # "answer ONLY using facts"
