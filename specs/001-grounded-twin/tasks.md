---

description: "Task list for Grounded Twin (Phase 1)"
---

# Tasks: Grounded Twin

**Input**: Design documents from `/specs/001-grounded-twin/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/
**Tests**: INCLUDED — the feature requires an eval suite (US3) and the constitution mandates
tests-first (Principle V). Write tests/eval cases before the implementation they cover.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (from spec.md); Setup/Foundational/Polish have no story label
- Exact file paths are included in each task.

## Path conventions (from plan.md — single Python project)

`app.py`, `core/`, `corpus/`, `evals/`, `tests/` at repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project skeleton and dependencies.

- [ ] T001 Create the source layout per plan.md: `core/__init__.py`, `core/corpus_loader.py`, `core/prompt.py`, `core/llm_client.py`, and empty dirs `corpus/`, `evals/`, `tests/` (files may be stubs).
- [ ] T002 Create `requirements.txt` pinning `gradio`, `anthropic`, `openai`, `pyyaml`, `pytest`.
- [ ] T003 [P] Create `.env.example` listing `LLM_PROVIDER` and `LLM_API_KEY` (names only, no values).
- [ ] T004 [P] Create a `Dockerfile` that installs `requirements.txt` and runs `app.py`, with Gradio listening on `0.0.0.0:$PORT` (Cloud Run sets `$PORT`, default 8080).
- [ ] T005 [P] Add tooling config (`ruff`/formatter) and a `pytest` config (e.g. `pyproject.toml`) at repo root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared `core/` primitives every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 [P] Write failing unit test `tests/test_corpus_loader.py`: asserts all `corpus/*.md` are concatenated in sorted order, empty corpus raises, and an over-budget corpus warns.
- [ ] T007 Implement `core/corpus_loader.py` `load_corpus(folder="corpus") -> str` to satisfy T006 (concatenate sorted `*.md`, raise on empty, warn if token estimate > ~15k) per contracts/core-interface.md.
- [ ] T008 [P] Write failing unit test `tests/test_llm_client.py`: asserts provider selection from `LLM_PROVIDER`, missing env raises a clear error, and `stream()` yields chunks (SDKs mocked).
- [ ] T009 Implement `core/llm_client.py` `LLMClient` (reads `LLM_PROVIDER`/`LLM_API_KEY`, provider-agnostic `stream(system, history, message)`, typed error on provider failure that carries no secret) to satisfy T008.
- [ ] T010 [P] Create seed corpus files `corpus/resume.md`, `corpus/linkedin.md`, `corpus/about.md`, `corpus/self_interview.md` (scaffold `self_interview.md` with 10–20 first-person Q&A prompts) with structure/headings and placeholder notes. *(Real content authored by the maintainer — see Notes; résumé/LinkedIn drafted from `resources/*.pdf`.)*
- [ ] T011 Wire `core/__init__.py` to export the current public surface (`load_corpus`, `LLMClient`); it will be extended in US1 (`build_system_prompt`, `answer`).

**Checkpoint**: Corpus can be loaded and the LLM client streams — user stories can begin.

---

## Phase 3: User Story 1 - Grounded answers (Priority: P1) 🎯 MVP

**Goal**: A visitor can chat with the twin and get correct, first-person answers drawn only
from the corpus, streamed back.

**Independent Test**: Run `python app.py`, ask an in-corpus question, confirm the answer is
accurate to the corpus and reads naturally in first person.

### Tests for User Story 1 ⚠️ (write first, ensure they fail)

- [ ] T012 [P] [US1] Add the **grounded** eval cases (`expect: grounded`) to `evals/cases.yaml` per contracts/eval-cases-schema.md (questions whose answers are in the seed corpus).
- [ ] T013 [P] [US1] Write failing unit test `tests/test_prompt.py`: `build_system_prompt(corpus)` includes the full corpus text and the persona/first-person instruction.

### Implementation for User Story 1

- [ ] T014 [US1] Implement `core/prompt.py` `build_system_prompt(corpus_text)` — persona (first person, warm, concise) + honesty guardrail rules + full corpus — to satisfy T013.
- [ ] T015 [US1] Implement `core/answer(message, history)` in `core/` and export it from `core/__init__.py`: build the system prompt once, stream a grounded reply via `LLMClient`; return a "ask me a question" response for empty/whitespace input (edge case) without calling the model.
- [ ] T016 [US1] Implement `app.py` — Gradio `ChatInterface` that calls `core.answer` and streams chunks; catch `LLMClient` errors and show a friendly message (no stack trace/secret) per FR-012.
- [ ] T017 [US1] Validate the grounded scenario from quickstart.md (in-corpus question → correct first-person streamed answer; multi-turn follow-up stays coherent).

**Checkpoint**: The twin is live-able and answers grounded questions — a demonstrable MVP.

---

## Phase 4: User Story 2 - Honest refusal (Priority: P1)

**Goal**: When asked something the corpus doesn't cover, the twin explicitly declines and
offers in-scope topics instead of fabricating.

**Independent Test**: Ask an out-of-corpus question (e.g. an opinion never stated) and confirm
the twin declines honestly and offers alternatives; try a leading prompt and confirm it stays
grounded.

### Tests for User Story 2 ⚠️ (write first, ensure they fail)

- [ ] T018 [P] [US2] Add the **refusal** eval cases (`expect: refuse`) to `evals/cases.yaml`, including at least one adversarial/leading prompt, per contracts/eval-cases-schema.md.
- [ ] T019 [P] [US2] Write failing test `tests/test_refusal.py`: with a corpus lacking a topic, `core.answer` on that topic returns the decline signal and no fabricated fact (LLM mocked or a live-guardrail integration marker).

### Implementation for User Story 2

- [ ] T020 [US2] Strengthen the honesty guardrail in `core/prompt.py`: explicit "I don't have that information" decline, an offer of in-scope topics, and resistance to leading/adversarial prompts (FR-003, FR-004).
- [ ] T021 [US2] Make the decline phrasing a consistent, documented signal the eval runner can detect (align wording with contracts/eval-cases-schema.md refusal detection).

**Checkpoint**: Both P1 stories work — the twin answers grounded questions and refuses the rest.

---

## Phase 5: User Story 3 - Provable eval gate (Priority: P2)

**Goal**: A repeatable evaluation reports the grounded-answer rate and refusal rate and fails
when thresholds aren't met, protecting against regressions.

**Independent Test**: Run `python evals/run_evals.py`; confirm it prints both rates and the
failing cases, and exits non-zero if `grounded_rate < 90%` or `refusal_rate < 100%`.

### Implementation for User Story 3

- [ ] T022 [US3] Implement `evals/run_evals.py`: load `evals/cases.yaml`, run each case via `core.answer(q, history=[])`, classify grounded vs refusal per the schema, and compute the `EvalReport` fields from data-model.md.
- [ ] T023 [US3] Add report output (grounded_rate, refusal_rate, list of failures) and set exit code non-zero when `grounded_rate < 90%` OR `refusal_rate < 100%` (SC-001/SC-002).
- [ ] T024 [P] [US3] Add CI workflow `.github/workflows/ci.yml` running `pytest` and `python evals/run_evals.py` on push/PR.
- [ ] T025 [US3] Validate the gate end-to-end: with the authored corpus, `run_evals.py` reports rates and passes both thresholds.

**Checkpoint**: Groundedness is provable and regression-safe.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T026 [P] Update `README.md` overview and link the quickstart; ensure `.env.example` lists every required variable.
- [ ] T027 Secrets audit: confirm no secret is present in the working tree or git history and that `.gitignore` covers `.env`, `resources/`, and `docs/private/` (Principle IV, SC-005).
- [ ] T028 Deploy to **Google Cloud Run**: store `LLM_API_KEY` in Secret Manager, grant the service account access, and `gcloud run deploy --source .` with `--set-secrets`/`--set-env-vars` (per quickstart.md).
- [ ] T029 Smoke-test the public Space URL: one grounded question and one out-of-corpus question behave correctly (SC-003).
- [ ] T030 [P] Run all quickstart.md validation scenarios and record results.

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (P1)** → no dependencies.
- **Foundational (P2)** → depends on Setup; **blocks all user stories**.
- **US1 (P3)** → depends on Foundational. The MVP.
- **US2 (P4)** → depends on Foundational; builds on the US1 prompt/answer path but is
  independently testable via its own refusal cases.
- **US3 (P5)** → depends on `core.answer` existing (US1) and on refusal behavior (US2) to
  exercise both rate types; the runner itself is independent code.
- **Polish (P6)** → after the desired stories; deploy (T028) after US1 at minimum.

### Within each story

- Tests/eval cases written first and failing → then implementation.
- `prompt.py` before `answer()` before `app.py`.

### Parallel opportunities

- Setup: T003, T004, T005 in parallel.
- Foundational: T006 ∥ T008 ∥ T010 (different files); each impl follows its test.
- US1: T012 ∥ T013. US2: T018 ∥ T019.
- US3: T024 (CI) parallel with runner validation.

---

## Parallel Example: Foundational

```bash
# Write the failing unit tests together (different files):
Task: "tests/test_corpus_loader.py"        # T006
Task: "tests/test_llm_client.py"           # T008
Task: "seed corpus files corpus/*.md"      # T010
```

---

## Implementation Strategy

### MVP first (US1 only)

1. Phase 1 Setup → 2. Phase 2 Foundational → 3. Phase 3 US1 → **STOP & validate** a grounded
   conversation → optionally deploy (T028) for an early live demo.

### Incremental delivery

Foundational → **US1 (grounded, MVP)** → **US2 (honest refusal)** → **US3 (eval gate)** →
Polish/deploy. Each step is independently testable and adds value without breaking the last.

---

## Notes

- **The corpus is the real work.** T010 only scaffolds the files; meaningful eval pass rates
  (SC-001/SC-002) depend on the maintainer authoring real content — especially
  `corpus/self_interview.md` (10–20 first-person Q&A). This is the cold-start unlock and is a
  prerequisite for T017/T025 to be meaningful.
- [P] = different files, no incomplete dependencies.
- Commit after each task or logical group; never commit a secret (Principle IV).
- Keep `core/` free of any UI import (Principle II) — verify in review.
