from __future__ import annotations

from app.services.analysis import MarketResearchAnalyzer
from app.services.llm.chain_factory import build_article_analysis_chain
from app.services.llm.models import JudgeResult, MarketIntelligenceReport


class BrokenLLM:
    def invoke(self, _value):
        raise RuntimeError("boom")


def test_analyze_articles_falls_back_when_llm_raises(monkeypatch):
    analyzer = MarketResearchAnalyzer.__new__(MarketResearchAnalyzer)
    analyzer.article_chain = BrokenLLM()
    analyzer.report_chain = BrokenLLM()
    analyzer.judge_chain = BrokenLLM()

    report, judge = analyzer.analyze_articles(
        scraped_articles=[{"article_text": "Sample article", "url": "https://example.com"}],
        competitors=["Acme"],
        topics=["AI"],
        context="",
    )

    assert isinstance(report, MarketIntelligenceReport)
    assert isinstance(judge, JudgeResult)
    assert report.executive_summary
    assert judge.hallucination_detection


def test_article_analysis_fallback_uses_article_text_not_prompt_text():
    class PromptLeakingLLM:
        def invoke(self, _value):
            raise RuntimeError("boom")

    chain = build_article_analysis_chain(PromptLeakingLLM())
    result = chain.invoke(
        {
            "article_text": "OpenAI announced a product launch and Anthropic expanded its partnerships.",
            "source_url": "https://example.com/article",
            "competitors": ["OpenAI", "Anthropic"],
            "topics": ["AI models"],
            "context": "",
        }
    )

    assert "OpenAI announced a product launch" in result.executive_summary
    assert "Return a JSON object with these keys only" not in result.executive_summary
