# Implementation Plan: Grounded Twin

**Branch**: `001-grounded-twin` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-grounded-twin/spec.md`

## Summary

Build a conversational AI "digital twin" that answers questions about Sridhar strictly from
a curated Markdown corpus, honestly declines anything the corpus doesn't cover, and is
verified by an eval suite (grounded-answer rate + refusal rate). Technical approach: a
UI-agnostic Python `core/` package (corpus loader → prompt builder with an honesty guardrail
→ provider-agnostic LLM client) with the entire corpus context-stuffed into the system
prompt (no retrieval). A thin Gradio `app.py` chat shell calls `core/` in-process. Deployed
free to Google Cloud Run (scale-to-zero container); secrets come only from Google Secret
Manager (prod) / local `.env`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `gradio` (UI), `anthropic` and/or `openai` (LLM SDKs behind a
provider-agnostic client), `pyyaml` (eval cases), `pytest` (tests). No web framework, no
database, no vector store.

**Storage**: Flat Markdown files under `corpus/` (source of truth). No database.

**Testing**: `pytest` for unit tests; a dedicated eval runner (`evals/run_evals.py`) over
`evals/cases.yaml`.

**Target Platform**: Google Cloud Run (Linux container, scale-to-zero). Also runs locally via
`python app.py`.

**Project Type**: Single Python project — an application (thin UI over a `core/` library),
not a web service or multi-package repo.

**Performance Goals**: Interactive chat; responses stream token-by-token so time-to-first-
token is perceptible quickly. Latency is dominated by the LLM provider. The system prompt
(persona + guardrail + corpus) is assembled once at startup and reused. Low traffic
(personal site); no throughput target.

**Constraints**:
- Corpus MUST fit the model context budget (target ≤ ~15k tokens) — enforces "no RAG".
- `core/` MUST NOT import any UI library (keeps it portable/testable).
- No secret in the repository or its history; secrets read from environment only.
- Errors surface a friendly message; never leak stack traces or secrets.

**Scale/Scope**: Single subject (Sridhar), single language (English), anonymous visitors,
no accounts. ~6 small source files plus the corpus and eval set.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

> **Note:** Checked against the ratified constitution `.specify/memory/constitution.md`
> (v1.0.0, ratified 2026-09-08).

| Principle (constitution v1.0.0) | Gate | Status |
|---|---|---|
| **I. Grounded & Honest (NON-NEGOTIABLE)** | Answers only from corpus; explicit refusal otherwise; proven by evals | ✅ Enforced by prompt guardrail (§ prompt.py) + refusal eval cases (SC-002) |
| **II. Thin UI over a portable core** | All logic in `core/`; UI must not leak into it | ✅ `core/` has no Gradio import; `app.py` is a shell |
| **III. YAGNI / simplest thing** | No RAG, no DB, no HTTP API, single deployable | ✅ Context-stuffing; Gradio in-process |
| **IV. Secrets Hygiene (NON-NEGOTIABLE)** | No secret in repo; env-only | ✅ `.env`/Secret Manager; `.gitignore` covers it (SC-005) |
| **V. Small, single-purpose, tested modules** | Each unit one job, tests-first, evals green | ✅ loader / prompt / llm_client / app / evals separated |
| *(Agentic tools)* | Earned in a later phase; NOT in this feature | ✅ Correctly out of scope here (YAGNI) |

**Result:** PASS — no violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-grounded-twin/
├── plan.md              # This file
├── research.md          # Phase 0 output — decisions & rationale
├── data-model.md        # Phase 1 output — entities
├── quickstart.md        # Phase 1 output — run/validate/deploy guide
├── contracts/           # Phase 1 output — internal interface contracts
│   ├── core-interface.md
│   └── eval-cases-schema.md
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
app.py                   # Gradio ChatInterface shell — thin UI, calls core/ only
core/
├── __init__.py          # exposes the public core interface (see contracts/core-interface.md)
├── corpus_loader.py     # read + concatenate corpus/*.md
├── prompt.py            # build_system_prompt(): persona + honesty guardrail + corpus
└── llm_client.py        # provider-agnostic streaming client (anthropic | openai)

corpus/                  # source of truth (Markdown)
├── resume.md
├── linkedin.md
├── about.md
└── self_interview.md    # 10–20 first-person Q&A (cold-start unlock; grow over time)

evals/
├── cases.yaml           # grounded + refusal cases (see contracts/eval-cases-schema.md)
└── run_evals.py         # runs cases against core/, reports rates

tests/
├── test_corpus_loader.py
├── test_prompt.py
└── test_llm_client.py   # provider selection (mocked SDKs)

README.md                # project overview
Dockerfile               # container for Cloud Run (runs app.py on $PORT)
requirements.txt
.env.example             # names of required env vars (no values)
```

**Structure Decision**: Single Python project. The `core/` package is the portable asset;
`app.py` is a disposable UI shell. `evals/` and `tests/` sit at root. Corpus is data, not
code. This matches `docs/phase-1-design.md` and keeps every module single-purpose.

## Complexity Tracking

No constitution violations — section intentionally empty.
