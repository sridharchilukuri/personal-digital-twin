<!--
Sync Impact Report
- Version change: (unratified template) → 1.0.0
- Ratification type: Initial adoption
- Modified principles: none (first ratification)
- Added principles:
    I.   Grounded & Honest Above All (NON-NEGOTIABLE)
    II.  Thin UI Over a Portable Core
    III. YAGNI / Simplest Thing That Works
    IV.  Secrets Hygiene (NON-NEGOTIABLE)
    V.   Small, Single-Purpose, Tested Modules
- Added sections:
    - Additional Constraints & Quality Gates
    - Development Workflow
    - Governance
- Removed sections: none
- Templates reviewed:
    - plan.md Constitution Check → consistent (gates already map to these principles)
    - spec.md / tasks.md → no changes required
- Deferred TODOs: none
-->

# Personal Digital Twin Constitution

## Core Principles

### I. Grounded & Honest Above All (NON-NEGOTIABLE)

The twin MUST answer only from the curated corpus. When the corpus does not cover a
question, the twin MUST say so explicitly and MUST NOT invent facts, employers, dates,
titles, skills, or opinions. Groundedness is the product; a fabricated answer is a defect,
not a rough edge. This behavior MUST be verified by evaluations covering both correct
grounded answers and correct refusals — it is never merely asserted.

**Rationale**: The twin's entire value and credibility rest on being trustworthy. One
confident fabrication destroys that trust, so grounding is enforced and measured, not hoped
for.

### II. Thin UI Over a Portable Core

All real logic MUST live in a UI-agnostic core module that imports no UI framework. User
interfaces MUST be thin, swappable shells that call the core. The core MUST be reusable and
testable independently of any UI or host.

**Rationale**: The valuable, long-lived asset is the agent logic. Keeping it free of UI
concerns lets the interface change (or be replaced) without risking the substance, and keeps
the core directly testable.

### III. YAGNI / Simplest Thing That Works

The simplest approach that satisfies the requirement MUST be preferred. Complexity —
retrieval/RAG, databases, HTTP APIs, cloud infrastructure, additional services — MUST be
added only when a concrete, present need forces it. Context-stuffing is preferred over
retrieval until the corpus outgrows the context budget; managed/free hosting is preferred
over custom cloud infrastructure until a concrete need requires otherwise.

**Rationale**: Premature complexity is the main way small projects stall. Deferring it keeps
the system understandable, cheap, and fast to change.

### IV. Secrets Hygiene (NON-NEGOTIABLE)

No secret or credential may ever appear in the repository or its git history. Secrets MUST be
supplied only through environment variables or the host's secret storage. Errors surfaced to
users MUST NOT leak secrets or stack traces.

**Rationale**: A leaked key is unrecoverable once in history and can be costly or dangerous.
This is a bright line with no exceptions.

### V. Small, Single-Purpose, Tested Modules

Each module MUST do one job behind a clear interface and MUST be understandable and testable
in isolation. Eval/unit tests MUST be written before the implementation they cover. The eval
suite is the headline quality gate and MUST stay green; a change that breaks a refusal case
is a regression to be fixed, not tolerated.

**Rationale**: Small, well-bounded, test-first modules are easier to reason about, safer to
change, and make groundedness continuously verifiable.

## Additional Constraints & Quality Gates

- **Grounding budget**: The corpus MUST fit the model's context budget (target ≤ ~15k
  tokens). Exceeding it triggers a deliberate decision about retrieval — it is never handled
  by silently degrading grounding.
- **Eval thresholds** (release gate): grounded-answer rate MUST be ≥ 90% and out-of-corpus
  refusal rate MUST be 100%. The eval runner MUST fail (non-zero exit) when either threshold
  is unmet so CI blocks regressions.
- **Provider portability**: The language-model provider MUST be swappable via configuration
  without changing conversational behavior.
- **No secret in history**: Verified at every commit; source PDFs and private notes stay out
  of the published repository.

## Development Workflow

- Work proceeds through the Spec Kit cycle: `specify → plan → tasks → analyze → implement`,
  one cycle per phase.
- Every plan MUST include a Constitution Check gate evaluated against these principles before
  design and again after design.
- Tests (unit and evals) are written before the implementation they verify.
- Runtime development guidance for contributors and agents lives in `CLAUDE.md`.

## Governance

This constitution supersedes ad-hoc practice. Every plan MUST pass the Constitution Check
gate; any complexity that violates a principle MUST be justified in the plan's Complexity
Tracking section or removed. Amendments MUST be recorded by updating this file, bumping the
version per semantic versioning, and noting the change in the Sync Impact Report:

- **MAJOR**: backward-incompatible governance or principle removals/redefinitions.
- **MINOR**: a new principle/section added or materially expanded guidance.
- **PATCH**: clarifications, wording, or non-semantic refinements.

Compliance is reviewed whenever work is planned or merged; the NON-NEGOTIABLE principles
(I and IV) admit no exceptions.

**Version**: 1.0.0 | **Ratified**: 2026-09-08 | **Last Amended**: 2026-09-08
