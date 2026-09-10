"""Loads the curated corpus (corpus/*.md) into a single string.

Phase 1 grounding is context-stuffing: the whole corpus goes into the system prompt,
so this module just concatenates every Markdown file. No retrieval, no chunking.
"""

from __future__ import annotations

import warnings
from pathlib import Path

# Rough context budget. Beyond this, context-stuffing stops being appropriate and
# a retrieval (RAG) layer should be considered. ~4 chars per token is a crude estimate.
CONTEXT_BUDGET_TOKENS = 15_000
_CHARS_PER_TOKEN = 4


def load_corpus(folder: str = "corpus") -> str:
    """Concatenate all ``*.md`` files under ``folder``, sorted by filename.

    Raises:
        FileNotFoundError: the folder does not exist.
        ValueError: the folder contains no non-empty Markdown content.
    """
    root = Path(folder)
    if not root.is_dir():
        raise FileNotFoundError(f"Corpus folder not found: {folder}")

    parts: list[str] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            parts.append(f"===== {path.name} =====\n\n{text}")

    corpus = "\n\n".join(parts).strip()
    if not corpus:
        raise ValueError(
            f"Corpus is empty: no Markdown content found under {folder}. "
            "A twin with no corpus cannot answer anything."
        )

    estimated_tokens = len(corpus) // _CHARS_PER_TOKEN
    if estimated_tokens > CONTEXT_BUDGET_TOKENS:
        warnings.warn(
            f"Corpus is ~{estimated_tokens} tokens, over the ~{CONTEXT_BUDGET_TOKENS} "
            "context budget. Consider moving to retrieval (RAG).",
            stacklevel=2,
        )

    return corpus
