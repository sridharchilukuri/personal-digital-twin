# Phase 1 Data Model — Grounded Twin

The system has no database. "Data" here is: Markdown corpus files on disk, in-memory
conversation state during a session, and the eval case/report structures. This documents the
logical entities, their fields, and validation rules derived from the spec.

---

## Entity: Corpus

The full curated source of truth about the subject. Loaded once at startup.

| Field | Type | Notes |
|---|---|---|
| documents | list of CorpusDocument | all `corpus/*.md`, sorted by filename for stable ordering |
| text | string | concatenation of all documents' contents (what gets stuffed into the prompt) |
| token_estimate | integer | approximate token count of `text` |

**Validation rules**
- MUST be non-empty (at least one document with content) — an empty corpus makes the twin
  hollow.
- `token_estimate` SHOULD be ≤ the context budget (~15k). Exceeding it is a signal to revisit
  retrieval (not a Phase 1 feature), and SHOULD emit a warning at load time.

## Entity: CorpusDocument

One Markdown file under `corpus/`.

| Field | Type | Notes |
|---|---|---|
| name | string | filename, e.g. `resume.md` |
| content | string | raw Markdown text |

**Expected documents (FR-007)**: `resume.md`, `linkedin.md`, `about.md`, `self_interview.md`.
The loader is content-agnostic (any `*.md` is included), but these four are expected to exist.

## Entity: Conversation

The in-memory exchange for a single visitor session. Managed by the UI (Gradio history);
`core/` receives it per turn and is otherwise stateless.

| Field | Type | Notes |
|---|---|---|
| messages | ordered list of Message | full turn history for context (FR-006) |

**Validation rules**
- A new visitor message that is empty/whitespace-only MUST NOT be sent to the model; the twin
  prompts for a real question (edge case).

## Entity: Message

| Field | Type | Notes |
|---|---|---|
| role | enum | `user` \| `assistant` |
| content | string | message text |

## Entity: EvalCase

One evaluation item.

| Field | Type | Notes |
|---|---|---|
| q | string | the question to ask the twin |
| expect | enum | `grounded` (answer from corpus) \| `refuse` (out-of-scope) |
| note | string (optional) | human context, e.g. why this case exists |

**Validation rules**
- `q` non-empty; `expect` ∈ {`grounded`, `refuse`}.
- The set MUST contain both `grounded` and `refuse` cases (FR-009), 20–30 total.

## Entity: EvalReport

The aggregated result of running all EvalCases.

| Field | Type | Notes |
|---|---|---|
| total | integer | number of cases run |
| grounded_total / grounded_pass | integer | count + how many grounded cases answered correctly |
| refuse_total / refuse_pass | integer | count + how many out-of-scope cases correctly refused |
| grounded_rate | percentage | grounded_pass / grounded_total → gate SC-001 (≥ 90%) |
| refusal_rate | percentage | refuse_pass / refuse_total → gate SC-002 (= 100%) |
| failures | list | the specific cases that failed, for debugging |

**Pass condition**: `grounded_rate ≥ 90%` AND `refusal_rate == 100%`.

---

## Relationships

```
Corpus ──1..*── CorpusDocument         (corpus/*.md)
Conversation ──1..*── Message
EvalReport ──aggregates── EvalCase[]    (evals/cases.yaml)
Corpus ──feeds──► system prompt ──used by──► every answer & every EvalCase run
```
