from __future__ import annotations

from types import SimpleNamespace

from app.services.llm.chain_factory import build_article_analysis_chain, build_llm_chain


class BrokenGroq:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def invoke(self, _value):
        raise RuntimeError("429 rate limit reached")


def test_build_llm_chain_returns_fallback_payload_when_groq_is_rate_limited(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "dummy-key")
    monkeypatch.setenv("GROQ_MAX_RETRIES", "1")
    monkeypatch.setattr("app.services.llm.chain_factory.ChatGroq", BrokenGroq)

    llm = build_llm_chain()
    chain = build_article_analysis_chain(llm)
    payload = chain.invoke({
        "article_text": "OpenAI launched GPT-5.",
        "source_url": "https://example.com",
        "competitors": ["OpenAI"],
        "topics": ["LLM"],
        "context": "",
    })

    assert payload.executive_summary
    assert payload.key_themes
