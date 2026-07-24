"""Article chunking using LangChain's recursive text splitter."""
from __future__ import annotations

import re

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # Retain a usable fallback for partial local installations.
    RecursiveCharacterTextSplitter = None


def chunk_text(text: str, chunk_size: int = 5_000, overlap: int = 350) -> list[str]:
    """Split on paragraphs/sentences first, preserving context across chunks.

    RecursiveCharacterTextSplitter prefers natural language boundaries in this
    order: paragraphs, lines, sentences, words, then individual characters.
    """
    text = text.strip()
    if not text:
        return []
    if RecursiveCharacterTextSplitter is not None:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
            keep_separator=True,
        )
        return [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
