# Personal Digital Twin

An **agentic AI digital twin** — a personal website with an embedded AI persona that
answers questions grounded strictly in a curated corpus, honestly says when it doesn't
know, and takes real actions (booking meetings, sending email) through well-defined tools.

> **Status:** 🚧 In active development. Phase 1 (the grounded conversational twin) is
> designed and being built. See [`docs/spec-plan.md`](docs/spec-plan.md) for the roadmap.

---

## What makes it interesting

- **Grounded, not guessing.** The twin answers *only* from its corpus. Ask it something it
  doesn't know and it tells you so — it never fabricates. This behavior is enforced by an
  eval suite, not just a prompt.
- **Agentic.** Beyond conversation, the twin uses tools to take real-world action —
  checking a calendar and booking a meeting, or emailing a summary (Phase 2).
- **Provider-agnostic.** The language model sits behind a single `LLMClient` interface, so
  the backend can swap between providers (Claude, OpenAI) without touching the rest of the
  system.
- **Evaluated.** A committed test suite verifies both correct grounded answers and correct
  refusals of out-of-scope questions.

## Architecture

```
┌─────────────────────────┐        ┌──────────────────────────────┐
│  Frontend (Next.js/TS)  │  HTTP  │   Backend (FastAPI / Python) │
│  Minimal streaming chat │ ─────► │   /chat  → prompt + LLMClient │
│                         │ ◄───── │           + honesty guardrail │
└─────────────────────────┘        └──────────────┬───────────────┘
                                                  │
                                   ┌──────────────▼───────────────┐
                                   │  Corpus (Markdown, in repo)  │
                                   └──────────────────────────────┘
```

In Phase 1 the entire corpus is stuffed into the model's context (no RAG) — the corpus is
small enough to fit, and this keeps the system simple. A migration to retrieval (RAG) is
planned for when the corpus outgrows the context window.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| LLM | Provider-agnostic (Claude / OpenAI) |
| Frontend | Next.js, React, TypeScript |
| Corpus | Markdown, versioned in git |
| Tests / evals | pytest |

## Project structure

```
backend/    FastAPI app, LLMClient, prompt builder, honesty guardrail
frontend/   Next.js chat UI
corpus/     Source-of-truth Markdown about the subject
evals/      Grounded + refusal eval cases
docs/       Design and roadmap
```

## Documentation

- [`docs/phase-1-design.md`](docs/phase-1-design.md) — detailed design of the grounded twin.
- [`docs/spec-plan.md`](docs/spec-plan.md) — full phased roadmap.

## Getting started

> Setup instructions will land as the backend and frontend are scaffolded (Phase 1).

## License

TBD.
