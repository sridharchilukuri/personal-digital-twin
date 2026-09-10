# Quickstart — Grounded Twin

How to run, validate, and deploy the twin. This is a validation/run guide — implementation
detail lives in `tasks.md` and the code itself.

## Prerequisites

- Python 3.11+
- An LLM API key (Anthropic or OpenAI)
- A Google Cloud account + `gcloud` CLI (for deployment)

## Local setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# secrets via environment (never committed) — see .env.example for names
cp .env.example .env
# edit .env:  LLM_PROVIDER=anthropic|openai   LLM_API_KEY=sk-...
```

## Author the corpus (the real work)

Populate `corpus/` before expecting good answers:
- `resume.md`, `linkedin.md`, `about.md`, and especially `self_interview.md`
  (10–20 first-person Q&A pairs — the cold-start unlock; grow over time).

## Run locally

```bash
python app.py
# open the local URL Gradio prints; chat with the twin
```

**Expected**: streamed, first-person answers grounded in the corpus; out-of-corpus questions
are declined with an offer of in-scope topics.

## Validate — the quality gate

```bash
python evals/run_evals.py
```

**Expected output**: a report with `grounded_rate` and `refusal_rate` and any failures.
**Pass**: `grounded_rate ≥ 90%` AND `refusal_rate == 100%` (exit code 0). CI runs this on
every change; a new fabrication on a `refuse` case fails the build.

Unit tests:

```bash
pytest
```

## Validation scenarios (map to spec)

| Scenario | Action | Expected | Spec |
|---|---|---|---|
| Grounded answer | Ask an in-corpus question | Correct first-person answer from corpus | US1 / SC-001 |
| Honest refusal | Ask an out-of-corpus question | Explicit decline + in-scope offer, no fabrication | US2 / SC-002 |
| Multi-turn | Ask a context-dependent follow-up | Coherent within the conversation | US1 / SC-004 |
| Empty input | Send blank message | Prompt for a real question; no model call | Edge case |
| Provider error | Simulate an API failure | Friendly message; no stack trace/secret | FR-012 |
| Eval gate | Run `run_evals.py` | Rates reported; exits non-zero if thresholds unmet | US3 / SC-006 |

## Deploy to Google Cloud Run

1. One-time: create a GCP project, enable the Cloud Run + Secret Manager + Cloud Build APIs,
   install `gcloud`, and `gcloud auth login`.
2. Store the key in **Secret Manager** and grant the Cloud Run service account access:
   ```bash
   printf 'YOUR_KEY' | gcloud secrets create LLM_API_KEY --data-file=-
   gcloud secrets add-iam-policy-binding LLM_API_KEY \
     --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```
3. Deploy (Cloud Run builds the container from the `Dockerfile`):
   ```bash
   gcloud run deploy digital-twin --source . --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars=LLM_PROVIDER=anthropic \
     --set-secrets=LLM_API_KEY=LLM_API_KEY:latest
   ```
4. Smoke-test the public HTTPS URL with one grounded and one out-of-corpus question.

**Done when**: the public URL answers grounded questions correctly, refuses out-of-scope ones,
`run_evals.py` passes locally/CI, and no secret is present in git history.
