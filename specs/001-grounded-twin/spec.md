# Feature Specification: Grounded Twin

**Feature Branch**: `001-grounded-twin`

**Created**: 2026-09-08

**Status**: Draft

**Input**: User description: "Build the Phase 1 'Grounded Twin': a conversational AI digital twin of Sridhar Chilukuri, deployed live on a free public space. It answers questions about Sridhar grounded strictly in a curated corpus, honestly declines anything outside the corpus (never hallucinates), and is covered by an eval suite that verifies both correct grounded answers and correct refusals."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask about Sridhar and get grounded answers (Priority: P1)

A visitor (e.g. a recruiter or peer) opens the twin's public URL and asks questions about
Sridhar's background, experience, skills, or interests. The twin replies in first person as
Sridhar, using only facts drawn from the curated corpus, and streams the answer back
conversationally.

**Why this priority**: This is the core value of the product — a visitor learning about
Sridhar by conversation. Without it there is no twin. It is the minimum viable slice.

**Independent Test**: Open the live URL, ask a question whose answer is in the corpus (e.g.
"Where did Sridhar last work?"), and confirm the reply is accurate to the corpus and reads
naturally.

**Acceptance Scenarios**:

1. **Given** the twin is live, **When** a visitor asks a question covered by the corpus,
   **Then** the twin answers correctly using only corpus facts, in first person.
2. **Given** a multi-turn conversation, **When** the visitor asks a follow-up that relies on
   earlier context, **Then** the twin responds coherently within the same conversation.
3. **Given** any answer, **When** the visitor reads it, **Then** every factual claim is
   traceable to the corpus (no invented employers, dates, titles, or skills).

---

### User Story 2 - Honest refusal when the corpus is silent (Priority: P1)

A visitor asks something the corpus does not cover (e.g. "What is Sridhar's opinion on
Rust?" when he has never mentioned it). The twin explicitly acknowledges it doesn't know
rather than guessing, and offers to help with topics it does cover.

**Why this priority**: Groundedness is the product's credibility. A twin that fabricates is
worse than no twin. This behavior is co-equal P1 with answering — the two together define
"grounded."

**Independent Test**: Ask a question deliberately outside the corpus and confirm the twin
declines honestly and does not fabricate an answer.

**Acceptance Scenarios**:

1. **Given** a question with no supporting corpus content, **When** the visitor asks it,
   **Then** the twin states it doesn't have that information and does not invent an answer.
2. **Given** an out-of-scope question, **When** the twin declines, **Then** it offers
   in-scope alternatives (e.g. experience, projects, interests).
3. **Given** a leading or adversarial prompt attempting to elicit fabrication, **When** the
   visitor sends it, **Then** the twin stays grounded and refuses to invent facts.

---

### User Story 3 - Verify groundedness with an eval suite (Priority: P2)

The maintainer (Sridhar) runs a repeatable evaluation that checks the twin against a fixed
set of questions — some answerable from the corpus, some deliberately not — and gets a
pass/fail report proving the twin answers grounded questions and refuses out-of-scope ones.

**Why this priority**: This makes groundedness *provable and regression-safe*, not just a
one-time impression. It gates every change. P2 because it supports P1, but it is required
before the twin can be trusted to stay grounded over time.

**Independent Test**: Run the eval suite locally; confirm it reports the pass rate for
grounded cases and the refusal rate for out-of-scope cases.

**Acceptance Scenarios**:

1. **Given** the eval set, **When** the suite runs, **Then** it reports the percentage of
   in-corpus questions answered correctly and the percentage of out-of-corpus questions
   correctly refused.
2. **Given** a change that causes the twin to fabricate on a previously-refused question,
   **When** the suite runs, **Then** that case fails and the regression is visible.

---

### Edge Cases

- **Empty / whitespace input**: the twin prompts the visitor to ask a question rather than
  producing an answer.
- **Corpus partially covers the question**: the twin answers the covered part and is clear
  about what it doesn't know, rather than extrapolating.
- **Provider/backend error or timeout**: the visitor sees a friendly, non-technical message;
  no stack trace or secret is ever exposed.
- **Question in a language other than the corpus language**: the twin responds gracefully
  within its known scope rather than fabricating.
- **Very long conversation**: the twin continues to behave within its grounded scope.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST answer visitor questions about Sridhar using only information
  contained in the curated corpus.
- **FR-002**: The system MUST answer in the first person, as Sridhar, in a warm and concise
  tone.
- **FR-003**: When a question is not covered by the corpus, the system MUST explicitly state
  that it does not have that information and MUST NOT fabricate an answer.
- **FR-004**: When declining, the system MUST offer in-scope topics the visitor can ask
  about instead.
- **FR-005**: The system MUST stream responses back to the visitor conversationally.
- **FR-006**: The system MUST maintain coherence across turns within a single conversation.
- **FR-007**: The curated corpus MUST include Sridhar's résumé, professional profile,
  personal interests, and a self-interview of first-person question/answer pairs.
- **FR-008**: The system MUST expose a repeatable evaluation that reports both the
  correct-answer rate on in-corpus questions and the correct-refusal rate on out-of-corpus
  questions.
- **FR-009**: The evaluation MUST include both in-corpus questions (expected: grounded
  answer) and deliberately out-of-corpus questions (expected: refusal).
- **FR-010**: The system MUST be reachable by the public at a shareable URL.
- **FR-011**: Credentials required to run the twin MUST NOT be stored in the source
  repository; they MUST be supplied through the hosting environment's secret storage.
- **FR-012**: On any internal error, the system MUST present a friendly message to the
  visitor without exposing technical details or secrets.
- **FR-013**: The system MUST allow the underlying language-model provider to be changed via
  configuration without changing the conversational behavior.

### Key Entities *(include if feature involves data)*

- **Corpus**: The curated source of truth about Sridhar — résumé, professional profile,
  personal interests, and self-interview Q&A. All answers derive from it.
- **Conversation**: An ordered exchange of visitor messages and twin replies within a single
  session; provides context for follow-ups.
- **Eval Case**: A question paired with its expected behavior — either "answer from corpus"
  or "refuse as out-of-scope."
- **Eval Report**: The aggregated pass/fail result across all eval cases, including the
  grounded-answer rate and the refusal rate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The twin correctly answers at least 90% of in-corpus evaluation questions.
- **SC-002**: The twin correctly refuses 100% of deliberately out-of-corpus evaluation
  questions (zero fabricated answers tolerated).
- **SC-003**: The twin is reachable by anyone at a public URL.
- **SC-004**: A visitor can hold a coherent multi-turn conversation and receive streamed
  responses without needing any instructions.
- **SC-005**: No secret or credential appears anywhere in the source repository's history.
- **SC-006**: The evaluation can be run on demand and produces a clear pass/fail report of
  the grounded-answer rate and refusal rate.

## Assumptions

- The corpus is small enough to be provided to the model in full for each question; no
  retrieval/search system is needed at this stage.
- A single subject (Sridhar) and a single language (English) are in scope.
- The primary corpus content — especially the self-interview Q&A — will be authored by
  Sridhar; the quality of answers depends on the depth of that content.
- Visitors are anonymous; there are no user accounts, authentication, or personalization.
- Analytics, usage tracking, and moderation tooling are out of scope for this feature.
- The hosting environment provides free public hosting and secure secret storage.
- A visitor has a modern web browser and internet connectivity.
