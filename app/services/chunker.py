from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger("market_research_api")

# Maximum characters per chunk — roughly 3 000 tokens for llama-3.3-70b
_DEFAULT_MAX_CHARS = 12_000


class TextChunker:
    """Split large article texts into token-safe chunks for LLM processing."""

    def __init__(self, max_chars: int = _DEFAULT_MAX_CHARS) -> None:
        self.max_chars = max_chars

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def split_into_chunks(self, text: str) -> List[str]:
        """Split *text* on paragraph boundaries so each chunk ≤ max_chars.

        Paragraphs that individually exceed max_chars are hard-split at the
        nearest sentence boundary (period + space).
        """
        if not text:
            return []

        if len(text) <= self.max_chars:
            return [text]

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []
        current_parts: List[str] = []
        current_len = 0

        for para in paragraphs:
            # If the paragraph alone is larger than the limit, split it further
            if len(para) > self.max_chars:
                # Flush current buffer first
                if current_parts:
                    chunks.append("\n\n".join(current_parts))
                    current_parts, current_len = [], 0
                # Hard-split on sentence boundaries
                sub_chunks = self._sentence_split(para)
                chunks.extend(sub_chunks)
                continue

            # Would adding this paragraph exceed the limit?
            prospective = current_len + len(para) + (2 if current_parts else 0)
            if prospective > self.max_chars and current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts, current_len = [], 0

            current_parts.append(para)
            current_len += len(para) + (2 if len(current_parts) > 1 else 0)

        if current_parts:
            chunks.append("\n\n".join(current_parts))

        return chunks or [text[: self.max_chars]]

    def chunk_articles(self, articles: List[dict]) -> List[dict]:
        """Return a flat list of chunk dicts for all articles.

        Each item: ``{"url": str, "chunk_index": int, "total_chunks": int, "article_text": str}``
        """
        result: List[dict] = []
        for article in articles:
            url = article.get("url", "")
            full_text = article.get("article_text", "")
            chunks = self.split_into_chunks(full_text)
            total = len(chunks)
            for idx, chunk in enumerate(chunks):
                result.append(
                    {
                        "url": url,
                        "chunk_index": idx,
                        "total_chunks": total,
                        "article_text": chunk,
                    }
                )
            logger.debug("Article %s split into %d chunk(s)", url, total)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sentence_split(self, text: str) -> List[str]:
        """Split *text* into max_chars pieces, preferring sentence ends."""
        chunks: List[str] = []
        while len(text) > self.max_chars:
            # Find the last period + space before the limit
            boundary = text.rfind(". ", 0, self.max_chars)
            if boundary == -1:
                boundary = self.max_chars
            else:
                boundary += 1  # include the period
            chunks.append(text[:boundary].strip())
            text = text[boundary:].strip()
        if text:
            chunks.append(text)
        return chunks
