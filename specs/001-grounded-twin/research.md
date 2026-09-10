# Phase 0 Research — Grounded Twin

The design was locked before planning (see `docs/phase-1-design.md`), so there are no open
`NEEDS CLARIFICATION` items. This file records the key decisions with rationale and the
alternatives considered.

---

## D1 — Grounding strategy: context-stuffing (no RAG)

- **Decision**: Concatenate the entire corpus into the system prompt for every request.
- **Rationale**: The corpus (résumé + profile + interests + self-interview) is small — target
  ≤ ~15k tokens — well within a modern model's context window. Retrieval adds a vector store,
  chunking, and embedding calls for no benefit at this size.
- **Alternatives considered**:
  - *RAG (embeddings + vector search)* — rejected as premature; correct only once the corpus
    outgrows the context budget.
  - *Fine-tuning on the corpus* — rejected: expensive, slow to iterate, and prone to
    hallucination/blurring of facts; the opposite of what "grounded" needs.
- **Trigger to revisit**: corpus token count exceeds the budget → plan a retrieval layer
  inside `core/`.

## D2 — Honesty guardrail: prompt-enforced, eval-verified

- **Decision**: Instruct the model (in the system prompt) to answer only from the corpus and
  to explicitly decline otherwise; verify the behavior with dedicated out-of-corpus eval
  cases.
- **Rationale**: The guardrail is the product's credibility. Instruction-following handles the
  behavior; evals turn "it should" into "it provably does," and catch regressions.
- **Alternatives considered**:
  - *Post-hoc answer verification / a second "grounding checker" model call* — rejected for
    Phase 1 as added latency/cost/complexity; the prompt+eval approach is sufficient at this
    scale and can be added later if evals reveal leakage.
  - *Trusting the prompt without evals* — rejected: unverifiable and regression-prone
    (violates the project's core principle).

## D3 — UI: Gradio `ChatInterface` over a UI-agnostic `core/`

- **Decision**: Use Gradio's `ChatInterface` as a thin shell in `app.py`; all logic lives in
  `core/`, which imports no UI library.
- **Rationale**: Fastest path to a live, streaming, mobile-friendly chat with zero frontend
  code — all Python, matching the backend. Keeping `core/` UI-agnostic makes the UI
  disposable and the logic reusable.
- **Alternatives considered**:
  - *Custom Next.js/React UI now* — rejected: much more work for polish that isn't needed
    until a later public-launch phase.
  - *Streamlit* — viable, but Gradio's `ChatInterface` is more purpose-built for chat +
    streaming and is first-class on the chosen host.

## D4 — Hosting: Google Cloud Run (scale-to-zero container)

- **Decision**: Deploy the container to **Google Cloud Run**; secrets from **Google Secret
  Manager**. Build/deploy via `gcloud run deploy --source .`.
- **Rationale**: Cloud Run's perpetual free tier (2M req/mo, ~50 CPU-hours) plus scale-to-zero
  means a low-traffic app costs ~$0, and the free tier is shared across a whole fleet of future
  apps. Any Docker container runs unchanged; native Secret Manager integration; public HTTPS
  URL. Better long-term fit than per-app paid hosting.
- **Alternatives considered**:
  - *Hugging Face Space* — rejected: HF now requires the PRO ($9/mo) plan to create Gradio/
    Docker (compute) Spaces on personal accounts.
  - *AWS App Runner* — no scale-to-zero (~$5/mo per app); poor economics for a fleet. *Fargate*
    needs an ALB (~$16/mo). AWS's scale-to-zero option is Lambda, which is awkward for a
    streaming Gradio server.
  - *Vercel* — serverless/JS-first; can't host a persistent Python Gradio server. Reserved for
    a future TS/Next.js frontend, if any.
  - *Single VPS (Hetzner/Oracle)* — viable fixed-cost fleet host; kept as a fallback if
    per-request cold starts ever matter.

## D5 — Provider-agnostic LLM client

- **Decision**: A single `LLMClient` in `core/` exposes one streaming method; provider
  (`anthropic` | `openai`) and API key are read from environment variables
  (`LLM_PROVIDER`, `LLM_API_KEY`).
- **Rationale**: Portability and testability; enables a live provider swap without touching
  conversational behavior (FR-013). Env-based config keeps secrets out of code.
- **Default provider**: whichever the maintainer is actively learning with; the abstraction
  makes the default a config value, not a code change.
- **Alternatives considered**:
  - *Hard-coding one vendor SDK throughout* — rejected: couples behavior to a vendor and
    weakens testability.
  - *A heavyweight framework (LangChain/LlamaIndex)* — rejected as unnecessary abstraction for
    a single prompt + single call; hand-rolling the thin client is simpler and clearer.

## D6 — Secrets handling

- **Decision**: Secrets live only in the environment: Google Secret Manager in production
  (injected into the container as env vars by Cloud Run), a gitignored `.env` locally. A
  committed `.env.example` documents variable *names* only.
- **Rationale**: Satisfies the hard secrets-hygiene rule and SC-005 (no secret in git
  history).
- **Alternatives considered**:
  - *Committing keys / a config file with values* — rejected outright.

## D7 — Eval harness format

- **Decision**: `evals/cases.yaml` holds cases (`q` + `expect: grounded | refuse`);
  `evals/run_evals.py` runs each against `core/` and reports the grounded-answer rate and the
  refusal rate.
- **Rationale**: YAML is human-editable (easy to grow the set); the runner calls `core/`
  directly (no UI/HTTP needed), so it's fast and CI-friendly.
- **Refusal detection**: classify a response as a refusal via explicit signals defined in the
  runner (e.g. the guardrail's decline phrasing / an "unknown" marker), documented in
  `contracts/eval-cases-schema.md`.
- **Alternatives considered**:
  - *Hand-testing only* — rejected: not repeatable, no regression protection.
  - *A full eval framework* — deferred; a small purpose-built runner is enough at this scale.
