# Personal Digital Twin

A personal website with an embedded **AI "digital twin"** of Sridhar Chilukuri. Ask it
anything about his work, experience, or interests — it answers **only** from a curated corpus,
tells you honestly when it doesn't know, and stays on the subject of Sridhar.

The point of the project is **groundedness**: the twin is trustworthy because it never
fabricates, and that behavior is enforced by an eval suite, not just a prompt.

## What makes it interesting

- **Grounded & honest.** Answers come only from the corpus. Ask something it doesn't know and
  it says so — no fabrication. Enforced by evals.
- **Reasons over the whole corpus.** It synthesizes across résumé, profile, and self-interview,
  and does simple date math ("how long at Proofpoint?") using today's date — not just canned
  Q&A lookups.
- **Scoped, not a chatbot-for-everything.** Ask it to write SQL or do math and it politely
  declines — it's Sridhar's twin, not a general assistant.
- **Provider-agnostic.** The model sits behind one `LLMClient` interface; swap Claude ↔ OpenAI
  via env vars without touching anything else.
- **Small & portable.** UI-agnostic `core/` package; a thin FastAPI web shell; one container.

## Architecture

```
  Browser  ──HTTP──►  FastAPI (app.py)
                        ├─ serves the static site (web/)
                        └─ POST /api/chat  ─►  core/
                                                 ├─ corpus_loader  (reads corpus/*.md)
                                                 ├─ prompt         (persona + honesty/scope guardrail)
                                                 └─ llm_client     (Claude / OpenAI, streaming)
```

The entire corpus is stuffed into the model's context (no RAG) — it's small (~3k tokens), so
this is simplest and most reliable. RAG becomes worthwhile only if the corpus outgrows the
context budget (~15k tokens). See [`docs/design.md`](docs/design.md).

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| LLM | Provider-agnostic (Anthropic / OpenAI) |
| Frontend | Plain HTML / CSS / JS (streaming chat) |
| Corpus | Markdown, versioned in git |
| Tests / evals | pytest |
| Deploy | Docker → Google Cloud Run + Secret Manager |

## Project structure

```
app.py       FastAPI app: serves web/ + streaming /api/chat
core/        corpus_loader.py, prompt.py, llm_client.py  (UI-agnostic agent logic)
web/         index.html, style.css, app.js, assets/
corpus/      resume.md, linkedin.md, about.md, self_interview.md  (source of truth)
evals/       cases.yaml + run_evals.py  (grounded + refusal + off-topic gate)
tests/       pytest unit tests
docs/        design.md
Dockerfile
```

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then set LLM_PROVIDER and LLM_API_KEY
python app.py                 # open http://localhost:8080
```

Run the checks:

```bash
pytest                        # unit tests
python evals/run_evals.py     # the grounded/refusal quality gate
```

## Deploy (Google Cloud Run)

```bash
# store the key once
printf 'YOUR_KEY' | gcloud secrets create LLM_API_KEY --data-file=-

# deploy (Cloud Run builds the container from the Dockerfile)
gcloud run deploy digital-twin --source . --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars=LLM_PROVIDER=openai \
  --set-secrets=LLM_API_KEY=LLM_API_KEY:latest
```

Scale-to-zero means a low-traffic app costs ~$0. Details in [`docs/design.md`](docs/design.md).

## Future directions

- **Agentic actions** — let the twin take real actions through tools (e.g. book a meeting,
  send an email), turning "I don't know" into "want me to ask him and email you?"
- **RAG** — swap context-stuffing for retrieval if/when the corpus outgrows the context window.

## License

TBD.
