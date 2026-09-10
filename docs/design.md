# Design — Personal Digital Twin

A grounded, honest AI twin of Sridhar Chilukuri: a personal website whose chat answers only
from a curated corpus about him. This document explains how it's built and why.

## Goals

1. **Grounded & honest.** Answer only from the corpus; decline honestly otherwise; never
   fabricate. Prove it with evals.
2. **Scoped.** Only discuss Sridhar — not a general-purpose assistant.
3. **Simple & cheap to run and to grow into more apps** — one portable container, ~$0 hosting.

## Principles

- **Grounded & honest above all** — hallucination is a defect, verified by evals.
- **Scoped to Sridhar** — off-topic requests are declined.
- **Thin UI over a portable core** — all logic in `core/`, which imports no UI framework.
- **YAGNI** — context-stuffing before RAG; a single scale-to-zero container before cloud sprawl.
- **Secrets hygiene** — keys only in `.env` (local) / Secret Manager (prod); never committed.
- **Small, tested modules** — the eval suite is the headline quality gate.

## Architecture

```
  Browser ──HTTP──► FastAPI (app.py)
                      ├─ serves the static site (web/)
                      └─ POST /api/chat (streaming) ─► core.answer()
                                                          │
      corpus/*.md ──► core.load_corpus ──► core.build_system_prompt ──► core.LLMClient ──► LLM
                          (context-stuffed)     (persona + guardrail)    (Claude/OpenAI)
```

**`core/` — the portable heart (UI-agnostic):**
- `corpus_loader.py` — concatenates all `corpus/*.md` into one string; warns if it exceeds the
  context budget.
- `prompt.py` — builds the system prompt: persona + honesty/scope guardrail + today's date +
  the full corpus.
- `llm_client.py` — one streaming interface over Anthropic/OpenAI, selected by env vars.
- `__init__.py` — exposes `load_corpus`, `build_system_prompt`, `LLMClient`, `answer(...)`.

**`app.py` — a thin FastAPI shell** that serves `web/` and streams `core.answer()` over
`POST /api/chat`. It knows nothing about prompts or providers. The UI (`web/`) is plain
HTML/CSS/JS. Both are disposable; `core/` is the asset.

## How grounding works

The **entire corpus is placed in the system prompt** on every request (context-stuffing) —
no retrieval, no vector store. The corpus is ~3k tokens, well under a modern model's context
window, so this is the simplest and most reliable option: the model sees everything and there
is no retrieval step that can fetch the wrong chunk.

- **Trigger to revisit:** if the corpus approaches ~15k tokens, migrate to retrieval (RAG).
- **Bridge before RAG:** prompt caching (the system prompt is static) buys extra runway.

## The honesty & scope guardrail

The system prompt makes three behaviors non-negotiable, and the twin reasons over the *whole*
corpus rather than matching pre-written Q&A:

1. **Answer when supported** — synthesize across sections; make reasonable inferences and
   simple calculations from stated facts (e.g. durations from dates, using today's date).
2. **Decline honestly when the corpus is silent** — for a question *about Sridhar* it can't
   support: *"I don't have that in what Sridhar has shared."*
3. **Decline off-topic requests** — for anything not about Sridhar (math, code, trivia,
   chit-chat): *"I'm only here to talk about Sridhar."*

These two distinct decline phrases are also how the eval runner detects a correct refusal.

## Provider-agnostic LLM client

`LLMClient` reads `LLM_PROVIDER` (`anthropic` | `openai`) and `LLM_API_KEY` from the
environment and exposes one streaming method. Providers are swappable without touching
behavior. Any provider error is normalized to a typed `LLMError` that carries no secret or
stack trace; the UI shows a friendly message.

## Evals — the quality gate

`evals/cases.yaml` holds ~28 cases in three groups, run by `evals/run_evals.py` against
`core/`:

- **grounded** — answerable from the corpus (must answer),
- **refuse** — about Sridhar but absent from the corpus (must decline honestly),
- **off-topic** — not about Sridhar (must decline as out of scope).

The gate: **grounded ≥ 90%** and **refusal 100%** (a single fabrication fails the run with a
non-zero exit). This is the headline check and should run in CI on every change.

## Secrets

Secrets live only in the environment: a gitignored `.env` locally, Google Secret Manager in
production (injected into the container by Cloud Run). A committed `.env.example` documents
variable *names* only. Raw source material (résumé PDFs) and private notes are gitignored.

## Deployment

The app is a Docker container (`Dockerfile`) that runs `app.py` on `0.0.0.0:$PORT`. It deploys
to **Google Cloud Run** with `gcloud run deploy --source .`, pulling the key from Secret
Manager (see the README for the commands).

**Why Cloud Run over AWS?** The goal is many low-traffic apps at ~$0. Cloud Run **scales to
zero** and has a perpetual free tier shared across the account, so idle apps cost nothing.
AWS's container services (App Runner, Fargate) don't scale to zero cheaply, and Lambda is an
awkward fit for a long-running streaming web server. Because the app is a portable container,
it can still run on AWS (App Runner / ECS / EC2) whenever a project calls for it — nothing is
locked in.

## Testing

- **Unit tests** (`tests/`, pytest): corpus loader, prompt builder, provider selection, the
  `answer()` empty-input path, and refusal detection — all runnable without an API key (SDKs
  mocked).
- **Eval suite**: the grounded/refusal/off-topic gate above (needs a provider key).

## Future directions

- **Agentic actions** — give the twin tools (check a calendar and book a meeting, send an
  email), turning "I don't know" into "want me to ask him and email you his answer?"
- **RAG** — retrieval instead of context-stuffing, once the corpus earns it.
