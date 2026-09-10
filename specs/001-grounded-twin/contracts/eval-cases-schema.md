# Contract — Eval Cases Schema (`evals/cases.yaml`)

The eval set is the quality gate. It is data (YAML) so it can grow easily, and the runner
(`evals/run_evals.py`) executes it against `core/`.

## File shape

`evals/cases.yaml` is a list of case objects:

```yaml
- q: "Where did Sridhar last work?"
  expect: grounded
  note: "covered by resume.md"

- q: "What is Sridhar's opinion on Rust?"
  expect: refuse
  note: "not in corpus — must decline, not guess"
```

## Case fields

| Field | Required | Type | Meaning |
|---|---|---|---|
| `q` | yes | string (non-empty) | question asked to the twin |
| `expect` | yes | `grounded` \| `refuse` | required behavior |
| `note` | no | string | human context / why the case exists |

## Set-level rules

- 20–30 cases total (FR-009).
- MUST include both `grounded` and `refuse` cases.
- `refuse` cases MUST be things genuinely absent from the corpus (so a correct twin cannot
  answer them from grounding).

## Pass/fail semantics

For each case the runner obtains the twin's full response and classifies it:

- **`expect: grounded`** → passes if the response is a substantive answer (not a refusal).
  Stronger checks (expected keyword/fact present) MAY be added per case later.
- **`expect: refuse`** → passes if the response is a refusal — detected by the guardrail's
  decline signal (e.g. an explicit "I don't have that information" / "hasn't shared"
  phrasing), and does NOT fabricate an answer.

## Report (see data-model `EvalReport`)

The runner prints:
- `grounded_rate` = grounded_pass / grounded_total  → must be **≥ 90%** (SC-001)
- `refusal_rate` = refuse_pass / refuse_total        → must be **100%** (SC-002)
- the list of failing cases

Exit non-zero if either threshold is unmet (so CI blocks regressions).
