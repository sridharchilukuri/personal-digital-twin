"""Runs the eval cases against the twin and reports grounded-answer and refusal rates.

This is the headline quality gate (Constitution Principle V). It exits non-zero if the
grounded rate < 90% or the refusal rate < 100%, so CI blocks regressions.

Usage:  python evals/run_evals.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as `python evals/run_evals.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import LLMError, REFUSAL_MARKER, answer  # noqa: E402

CASES_FILE = Path(__file__).parent / "cases.yaml"
GROUNDED_THRESHOLD = 0.90  # SC-001
REFUSAL_THRESHOLD = 1.00   # SC-002

# Fallback phrases that also count as a refusal, in case the model paraphrases.
_REFUSAL_SIGNALS = (
    REFUSAL_MARKER.lower(),
    "don't have that",
    "hasn't shared",
    "haven't shared",
    "don't have information",
    "no information",
    "i don't know",
)


def is_refusal(text: str) -> bool:
    """True if the response reads as an honest 'I don't know', not a substantive answer."""
    low = text.lower()
    return any(sig in low for sig in _REFUSAL_SIGNALS)


def _full_answer(question: str) -> str:
    return "".join(answer(question, []))


def main() -> int:
    import yaml
    from dotenv import load_dotenv

    load_dotenv()
    cases = yaml.safe_load(CASES_FILE.read_text(encoding="utf-8"))

    grounded_total = grounded_pass = 0
    refuse_total = refuse_pass = 0
    failures: list[str] = []

    try:
        for case in cases:
            q, expect = case["q"], case["expect"]
            reply = _full_answer(q)
            refused = is_refusal(reply)

            if expect == "grounded":
                grounded_total += 1
                if not refused and reply.strip():
                    grounded_pass += 1
                else:
                    failures.append(f"[grounded→refused] {q}")
            elif expect == "refuse":
                refuse_total += 1
                if refused:
                    refuse_pass += 1
                else:
                    failures.append(f"[refuse→answered] {q}")
    except LLMError as exc:
        print(f"Could not run evals — LLM not configured: {exc}")
        print("Set LLM_PROVIDER and LLM_API_KEY (see .env.example) and retry.")
        return 2

    grounded_rate = grounded_pass / grounded_total if grounded_total else 1.0
    refusal_rate = refuse_pass / refuse_total if refuse_total else 1.0

    print("\n=== Eval Report ===")
    print(f"Grounded: {grounded_pass}/{grounded_total}  ({grounded_rate:.0%})  [gate ≥ 90%]")
    print(f"Refusal:  {refuse_pass}/{refuse_total}  ({refusal_rate:.0%})  [gate = 100%]")
    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  - {f}")

    passed = grounded_rate >= GROUNDED_THRESHOLD and refusal_rate >= REFUSAL_THRESHOLD
    print("\nRESULT:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
