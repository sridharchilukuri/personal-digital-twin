# Spec Plan — Grounded Twin (Phase 1)

**What we're building:** A conversational **AI "digital twin"** — an AI persona that answers
questions about Sridhar Chilukuri, grounded strictly in a curated corpus, honestly declines
what it doesn't know, and is live on a free public URL.

Detailed design is in `phase-1-design.md`. Later phases (agentic tools, a custom site) will
be planned when we get there — not documented ahead of time.

---

## Guiding principles

1. **Grounded & honest over impressive.** The twin answers ONLY from the corpus. When the
   corpus is silent, it says so — never invents facts. Hallucination is a defect.
2. **Thin UI over a portable core.** All real logic lives in a UI-agnostic `core/` package;
   the Gradio UI is a thin shell that just calls it.
3. **Simplest thing that works.** Context-stuffing (no RAG); Gradio + free Hugging Face
   Space (no cloud infra). Add complexity only when we actually need it.
4. **Small, testable modules** with clear interfaces.

---

## Build order

| # | Feature | Why in this order |
|---|---|---|
| 1.1 | Repo scaffold (`core/`, `corpus/`, `evals/`, `app.py`), git init, `.gitignore` | Foundation; secrets hygiene from commit 1 |
| 1.2 | **Corpus authoring** — `resume.md`, `linkedin.md`, `about.md`, **`self_interview.md` (50–100 Q&A)** | Cold-start unlock; blocks everything downstream |
| 1.3 | `core/corpus_loader.py` | Feeds the prompt |
| 1.4 | `core/llm_client.py` — provider-agnostic (Claude/OpenAI) | Core dependency |
| 1.5 | `core/prompt.py` — prompt builder + **honesty guardrail** | The core guarantee |
| 1.6 | **Eval harness** — `evals/cases.yaml` + `run_evals.py` (20–30 grounded + refusal cases) | Verifies no hallucination |
| 1.7 | `app.py` — Gradio `ChatInterface` shell over `core/` | The visible surface |
| 1.8 | Deploy to Hugging Face Space + CI running evals | Live and continuously verified |

**Done when:** ≥90% in-corpus eval questions answered correctly, 100% of out-of-corpus
questions declined, live on a Hugging Face Space URL, all in git with no secret committed.

---

## Dependency graph

```
1.1 scaffold
   └─ 1.2 corpus ─ 1.3 loader ─ 1.5 prompt/guardrail ─┬─ 1.6 evals
                         1.4 llm_client ──────────────┘   └─ 1.7 Gradio app ─ 1.8 deploy
```

---

## Spec Kit workflow

```
/speckit.specify     # feature spec from phase-1-design.md
/speckit.plan        # technical plan
/speckit.tasks       # ordered, dependency-aware tasks
/speckit.analyze     # consistency check before implement
/speckit.implement   # execute tasks
```

**Next step:** run `/speckit.specify`, feeding it `phase-1-design.md`.
