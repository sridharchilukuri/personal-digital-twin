# CLAUDE.md — Personal Digital Twin

Engineering context for AI collaborators (Claude Code and others). Read this first.

## What this is

A personal website with an embedded **AI "digital twin"** that answers questions *as Sridhar
Chilukuri*, grounded strictly in a curated corpus about him. It speaks only from what it
actually knows, says so plainly when it doesn't, and stays on the subject of Sridhar — it is
not a general-purpose assistant.

(A future direction is making it *agentic* — taking real actions like booking a meeting or
sending email through tools. Not built yet; see `docs/design.md`.)

## Non-negotiable principles

1. **Grounded & honest above all.** The twin answers ONLY from the corpus. When the corpus is
   silent, it says so — it never invents facts, employers, dates, skills, or opinions.
   Groundedness is the product; hallucination is a defect. This is verified by evals, not just
   asserted.
2. **Scoped to Sridhar.** The twin only discusses Sridhar. It declines off-topic requests
   (general knowledge, math, coding, chit-chat) rather than acting as a general assistant.
3. **Thin UI over a portable core.** All real logic lives in the UI-agnostic `core/` package.
   The web UI is a thin shell that just calls it.
4. **YAGNI / simplest thing that works.** Context-stuffing before RAG; a single scale-to-zero
   container before cloud sprawl. Add complexity only when a real need forces it.
5. **Secrets hygiene is a hard rule.** API keys live in a gitignored `.env` and the host's
   secret manager. Never commit a key.
6. **Small, single-purpose, tested modules** with clear interfaces.

## Current status

**Built and working locally.** The grounded conversational twin runs end-to-end: FastAPI +
web UI over the `core/` package, with the eval gate passing (grounded ≥90%, refusal 100%).
Not yet deployed publicly. See `docs/design.md` for the full design.

## Stack

- **Agent core:** Python `core/` package — UI-agnostic (no UI imports). Holds the
  provider-agnostic `LLMClient` (Claude ↔ OpenAI), the prompt builder + honesty/scope
  guardrail, and the corpus loader.
- **Web app:** **FastAPI** (`app.py`) — serves the static site in `web/` and a streaming
  `POST /api/chat` endpoint that calls `core/`. The UI (`web/`) is plain HTML/CSS/JS.
- **Hosting:** **Google Cloud Run** (scale-to-zero container); secrets via **Google Secret
  Manager** → env. Local dev via gitignored `.env`.
- **Corpus:** Markdown files in `corpus/`, context-stuffed into the system prompt. **No RAG.**
- **Evals:** pytest + `evals/run_evals.py` — grounded, refusal, and off-topic cases.

## Repo structure

```
app.py       FastAPI app: serves web/ + streaming /api/chat (thin — calls core/)
core/        corpus_loader.py, prompt.py, llm_client.py  (UI-agnostic agent logic)
web/         index.html, style.css, app.js, assets/  (the site)
corpus/      resume.md, linkedin.md, about.md, self_interview.md  (source of truth)
evals/       cases.yaml + run_evals.py  (grounded + refusal + off-topic gate)
tests/       pytest unit tests for core/
docs/        design.md
Dockerfile   container for Cloud Run
```

## Working conventions

- Follow existing patterns; keep modules small and single-purpose. `core/` must never import
  a UI/web framework.
- The **eval suite is the headline quality gate.** A change that breaks a refusal case is a
  regression — keep `python evals/run_evals.py` green.
- Write eval/unit tests alongside the code they cover.
- When the corpus approaches the context budget (~15k tokens), that is the deliberate trigger
  to plan a RAG migration. Flag it; don't over-engineer earlier.
- Use absolute dates in docs.
