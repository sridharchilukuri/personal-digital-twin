import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))

from run_evals import is_refusal  # noqa: E402


def test_detects_refusal_marker():
    assert is_refusal("I don't have that in what Sridhar has shared. Ask me about his work!")


def test_detects_paraphrased_refusal():
    assert is_refusal("Sridhar hasn't shared anything about that.")


def test_substantive_answer_is_not_a_refusal():
    assert not is_refusal("Sridhar is a Staff Software Engineer at Proofpoint.")
