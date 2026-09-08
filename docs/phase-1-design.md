# Phase 1 Design — Grounded Twin

**Status:** Design locked
**Goal of this phase:** Ship a conversational "digital twin" that answers questions
*grounded strictly in a curated corpus*, honestly declines what it doesn't know, is covered
by an eval harness that verifies it does not hallucinate, and is **live on a public URL**.

> This is the **walking skeleton**: the smallest thing that is genuinely useful and live.
> Anything not needed for that is deliberately left out (see §9). See `spec-plan.md` for the
> build order.

---

## 1. What Phase 1 delivers

A visitor opens a public URL, chats with the twin, and gets answers that are:

- **Grounded** — every claim traces back to the corpus (resume + LinkedIn + interests).
- **Honest** — asked something outside the corpus, the twin *says so* rather than guessing.
  (Phase 1 declines gracefully; Phase 2 upgrades "I don't know" into a real tool action.)
- **Provider-agnostic** — the LLM sits behind one interface so Claude ↔ OpenAI can be swapped.
- **Evaluated** — a committed eval suite asserts both correct grounded answers and correct
  refusals, and runs on every change.
- **Live** — deployed as a free Hugging Face **Gradio Space**.

**Success criteria (product quality):**
1. Twin correctly answers ≥90% of in-corpus eval questions.
2. Twin correctly *declines* 100% of deliberately out-of-corpus eval questions
   (zero hallucinations tolerated).
3. Reachable at a public Hugging Face Space URL.
4. Everything is versioned in git with a clean history; no secret ever committed.

---

## 2. Architecture — thin UI over a portable core

The guiding decision: **all real logic lives in a UI-agnostic `core/` package.** The UI
(Gradio) is a thin shell that only calls `core/`. This keeps the valuable part portable, so
the UI can be swapped later without touching the substance.

```
        ┌──────────────────────────────────────────────┐
        │  Hugging Face Space (free, Gradio SDK)        │
        │                                                │
        │   app.py  (Gradio ChatInterface — thin shell) │
        │        │ calls                                 │
        │        ▼                                        │
        │   core/  ── corpus_loader ─ prompt ─ llm_client│
        │        │                                        │
        │        ▼                                        │
        │   corpus/*.md  (context-stuffed, no RAG)       │
        │                                                │
        │   Secrets (LLM key) ← HF Space Secrets (env)   │
        └────────────────────────────────────────────────┘
```

**Single deployable.** No separate frontend, no HTTP API — Gradio calls `core/` in-process.

---

## 3. Components (each is an isolated unit with one job)

### 3.1 Corpus (`/corpus/`)
- **What it does:** Holds the source-of-truth about the subject as plain Markdown.
- **Files:** `resume.md`, `linkedin.md`, `about.md`, and `self_interview.md` — 50–100
  first-person Q&A pairs (**the cold-start unlock**; this is what lets the twin converse).
- **Dependency:** none. It's data.
- **Note:** The *entire* corpus is stuffed into the system prompt (context-stuffing).
  **No RAG.** Keep it within the model's context budget (target ≤ ~15k tokens). Outgrowing
  that is the trigger to migrate to RAG.

### 3.2 `core/corpus_loader.py`
- **What it does:** Concatenates every `corpus/*.md` into one string.
- **Depends on:** the filesystem only.

### 3.3 `core/prompt.py` — prompt builder + honesty guardrail
- **What it does:** Assembles the system prompt = persona + **honesty guardrail** + corpus.
- **Depends on:** corpus loader output.
- The honesty guardrail is the core guarantee (see §4).

### 3.4 `core/llm_client.py` — provider-agnostic interface
- **What it does:** Exposes one streaming method hiding the vendor; provider + key from env
  (`LLM_PROVIDER`, `LLM_API_KEY`).
- **Depends on:** the vendor SDK + env vars (which come from HF Space Secrets in prod).
- **Why:** keeps the system portable/testable and lets a live Claude↔OpenAI swap be shown.

### 3.5 `app.py` — Gradio shell (the throwaway UI)
- **What it does:** A `gr.ChatInterface` that streams `core/` output to the browser.
- **Depends on:** `core/`. Knows nothing about prompts or providers.
- **Deliberately minimal and disposable** — easy to swap out later.
- Handles provider/network errors with a graceful user-facing message; never leaks keys or
  stack traces.

### 3.6 Eval harness (`/evals/`)
- **What it does:** Runs a fixed set of question → expected-behavior cases against `core/`
  and asserts outcomes. `cases.yaml` (data) + `run_evals.py` (runner).
- **Cases (20–30):** a mix of (a) in-corpus questions with expected grounded facts, and
  (b) deliberately out-of-corpus questions where the *only* passing behavior is a refusal.
- **Depends on:** `core/` directly (not the UI).
- **Why it matters:** verifying "does it correctly refuse what it doesn't know?" is the core
  quality guarantee. Committed, visible, run before every push and in CI.

---

## 4. The honesty guardrail (the core guarantee)

The system prompt must make three things non-negotiable:
1. **Answer only from the provided corpus.** Never invent facts, dates, employers,
   opinions, or skills.
2. **When the corpus is silent, decline explicitly.** Name that it's unknown; offer
   in-scope alternatives.
3. **Stay in persona** — first-person, warm and concise.

Validated, not assumed: the out-of-corpus eval cases are the proof.

---

## 5. Data flow (a single chat turn)

1. Visitor types a message in the Gradio chat.
2. `app.py` calls `core/` with the message + prior history.
3. Corpus is loaded once at startup (system prompt built once and reused).
4. `LLMClient` streams the response from the configured provider.
5. Tokens stream back into the Gradio chat window.
6. On any provider error → graceful fallback message; error logged.

---

## 6. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Agent core | **Python** (`core/` package) | UI-agnostic; the portable asset |
| LLM | **Provider-agnostic**, configurable | Claude / OpenAI behind `LLMClient` |
| UI | **Gradio** (`gr.ChatInterface`) | Thin, all-Python, streaming built in; throwaway |
| Hosting | **Hugging Face Space (Gradio SDK)** | Free; sleeps when idle; public URL |
| Corpus | **Markdown in git** | Context-stuffed; no vector DB |
| Secrets | **HF Space Secrets → env vars** | Never in code or git |
| Tests | **pytest** + eval runner | Run locally + CI before each push |

---

## 7. Testing strategy

- **Unit:** prompt builder (corpus present in prompt), LLMClient provider selection,
  corpus loader.
- **Eval suite:** the 20–30 grounded/refusal cases — the headline test. Run locally and in
  CI on every change.
- **Manual smoke:** a short scripted walkthrough before each push to the Space.
- Tests-first where practical (write eval cases / unit tests before wiring implementation).

---

## 8. Deployment (Phase 1)

1. Author `corpus/*.md` (the real work — especially `self_interview.md`).
2. Create a Hugging Face **Space** → Gradio SDK; `README.md` YAML header configures it
   (`sdk: gradio`, `app_file: app.py`).
3. In **Space Settings → Secrets**, add `LLM_PROVIDER` and `LLM_API_KEY` (arrive as env
   vars; never in code).
4. `git push` the repo to the Space; HF builds and serves it at a public URL.
5. Locally (and in CI), run `evals/run_evals.py` before every push.

---

## 9. Explicitly OUT of scope (YAGNI)

Not building these now — only what's needed for a useful, live, grounded twin:

- ❌ RAG / vector DB (corpus fits in context).
- ❌ Agentic tools (calendar booking, email).
- ❌ Custom-branded website / HTTP API (Gradio calls `core/` in-process).
- ❌ Cloud infra / custom domain.
- ❌ Auth, user accounts, analytics.

---

## 10. Key risks

| Risk | Mitigation |
|---|---|
| **Thin corpus → hollow twin** (biggest risk) | Author `self_interview.md` (50–100 Q&A) *before/with* the code. |
| Hallucination on out-of-scope Qs | Honesty guardrail + out-of-corpus eval cases gating every change. |
| Leaked API keys | Secrets only in HF Space Secrets / local `.env` (gitignored); never committed. |
| UI logic leaking into `core/` | Keep `core/` free of any Gradio import — it must stay UI-agnostic and portable. |
| Corpus outgrows context | Track token count; revisit retrieval only if/when it exceeds the budget. |
