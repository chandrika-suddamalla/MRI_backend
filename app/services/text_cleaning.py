"""Cleaning of Trafilatura output before it enters an LLM context."""
from __future__ import annotations

import re


def clean_article_text(text: str) -> str:
    """Normalise whitespace while retaining all extracted article statements."""
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()
