# CLAUDE.md — Personal Digital Twin

Engineering context for AI collaborators (Claude Code and others). Read this first.

## What this is

An **agentic AI "digital twin"** — a personal website with an embedded AI persona that
answers questions *as Sridhar Chilukuri*, grounded strictly in a curated corpus about
him, and (from Phase 2 onward) takes real actions such as booking meetings and sending
email on his behalf.

The system is intentionally small and honest: it speaks only from what it actually
knows, and it says so when it doesn't.

## Non-negotiable principles

1. **Grounded & honest above all.** The twin answers ONLY from the corpus. When the
   corpus is silent, it says so — it never invents facts, employers, dates, skills, or
   opinions. Groundedness is the product; hallucination is a defect, not a rough edge.
2. **Agentic, not a chat wrapper.** The twin is designed to *take actions* through
   well-defined tools (earned in Phase 2), not merely to converse.
3. **YAGNI / simplest thing that works.** Context-stuffing before RAG. Use managed
   infrastructure for undifferentiated plumbing; hand-build the parts that carry the
   system's core value (retrieval loop, prompt construction, evals).
4. **Secrets hygiene is a hard rule.** API keys live in gitignored `.env` files and the
   host's secret manager. Never commit a key.
5. **Small, single-purpose modules** with clear interfaces that can be understood and
   tested independently.

## Current status

Design phase. Roadmap and Phase 1 design are written; **no application code exists yet.**

- `docs/phase-1-design.md` — full Phase 1 (Grounded Twin) design.
- `docs/spec-plan.md` — ordered roadmap across all phases + Spec Kit mapping.

**Build Phase 1 first.** Do not start Phase 2 (agentic tools) or Phase 3 (site polish)
until Phase 1 exit criteria are met.

## Stack (Phase 1)

- **Agent core:** Python `core/` package — UI-agnostic (no UI imports). Holds the
  provider-agnostic `LLMClient` (Claude ↔ OpenAI), prompt builder + honesty guardrail, and
  corpus loader.
- **UI:** **Gradio** (`gr.ChatInterface`) in `app.py` — a thin shell that only calls
  `core/`. Deliberately disposable.
- **Hosting:** **Google Cloud Run** (scale-to-zero container); secrets via **Google Secret Manager** → env. Local dev via gitignored `.env`.
- **Corpus:** Markdown files in `corpus/`, context-stuffed into the system prompt.
  **No RAG.**
- **Evals:** pytest + `evals/run_evals.py` — grounded-answer + refusal cases. Runs in CI.

## Repo structure

```
app.py      Gradio ChatInterface shell (thin UI — calls core/)
core/       llm_client.py, prompt.py, corpus_loader.py  (UI-agnostic agent logic)
corpus/     resume.md, linkedin.md, about.md, self_interview.md  (source of truth)
evals/      cases.yaml + run_evals.py  (grounded + refusal cases)
docs/       phase-1-design.md, spec-plan.md
```

## Workflow

Write eval/unit tests before wiring implementation.

## Working conventions

- Follow existing patterns; keep modules small and single-purpose.
- The **eval suite is the headline quality gate.** A change that breaks a refusal case is
  a regression — keep it green.
- When the corpus approaches the context budget (~15k tokens), that is the deliberate
  trigger to plan the RAG migration. Flag it; don't over-engineer earlier.
- Use absolute dates in docs.
