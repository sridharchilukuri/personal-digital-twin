# Contract — `core/` Public Interface

`core/` is the portable heart of the system. Every consumer — the Gradio UI now, the eval
runner, and any future UI — depends ONLY on this interface, never on the internals. `core/`
imports no UI library.

## Public surface (from `core/__init__.py`)

### `load_corpus(folder: str = "corpus") -> str`
- Reads every `*.md` under `folder`, sorted by filename, and returns their concatenated text.
- Raises if the folder is missing or yields empty content (a hollow corpus is a defect).
- SHOULD warn if the estimated token count exceeds the context budget (~15k).

### `build_system_prompt(corpus_text: str) -> str`
- Returns the full system prompt: persona instructions + the honesty guardrail + the corpus.
- The guardrail MUST instruct: answer only from the corpus; when the corpus is silent, decline
  explicitly and offer in-scope topics; stay in first person, warm and concise. (FR-001–004)

### `class LLMClient`
- `__init__(self)` — reads `LLM_PROVIDER` (`anthropic` | `openai`) and `LLM_API_KEY` from the
  environment. Raises a clear error if either is missing. (FR-011, FR-013)
- `stream(self, system: str, history: list[Message], message: str) -> Iterator[str]`
  - Yields response text chunks for streaming. (FR-005)
  - `history` is the prior conversation (see data-model `Message`).
  - Provider selection is internal; behavior is identical across providers.
  - On provider/network error, raises a typed error the caller maps to a friendly message
    (the client itself never emits secrets or stack traces). (FR-012)

### `answer(message: str, history: list[Message]) -> Iterator[str]`  *(convenience)*
- Top-level helper the UI and eval runner call. Loads/uses the prebuilt system prompt and
  streams the grounded reply for `message` given `history`.
- Empty/whitespace `message` yields a prompt-for-a-question response without calling the model
  (edge case).

## Consumer expectations

- **UI (`app.py`)**: builds the prompt once at startup (or relies on `answer`), then calls
  `answer(...)` per turn and streams chunks into the chat. Catches typed errors → friendly
  message.
- **Eval runner**: calls `answer(case.q, history=[])` and collects the full text to classify
  as grounded vs refusal.

## Invariants

- No function in `core/` imports `gradio` or any web/UI framework.
- No function prints or returns secrets.
- The system prompt always contains the full corpus (Phase 1 grounding = context-stuffing).
