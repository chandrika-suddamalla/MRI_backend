"""Groq-backed LangChain client construction."""
from __future__ import annotations
import os
from langchain_groq import ChatGroq


def get_groq_llm(chat_model_class=ChatGroq):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return chat_model_class(
        api_key=key,
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0,
        max_retries=int(os.getenv("GROQ_MAX_RETRIES", "2")),
    )
