import pytest

from core.corpus_loader import load_corpus


def test_concatenates_markdown_sorted(tmp_path):
    (tmp_path / "b.md").write_text("Bravo content", encoding="utf-8")
    (tmp_path / "a.md").write_text("Alpha content", encoding="utf-8")

    result = load_corpus(str(tmp_path))

    assert "Alpha content" in result
    assert "Bravo content" in result
    # sorted by filename: a.md before b.md
    assert result.index("Alpha content") < result.index("Bravo content")


def test_missing_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_corpus(str(tmp_path / "does-not-exist"))


def test_empty_corpus_raises(tmp_path):
    (tmp_path / "empty.md").write_text("   \n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_corpus(str(tmp_path))


def test_over_budget_warns(tmp_path):
    (tmp_path / "big.md").write_text("x" * 80_000, encoding="utf-8")  # ~20k tokens
    with pytest.warns(UserWarning):
        load_corpus(str(tmp_path))
