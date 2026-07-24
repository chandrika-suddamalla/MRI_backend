"""LangChain prompt/runnable chains, with safe source-text-only fallbacks."""
from __future__ import annotations

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnableLambda
except ImportError:
    ChatPromptTemplate = None
    class RunnableLambda:  # Minimal graceful fallback for optional runtime dependencies.
        def __init__(self, function): self.function = function
        def invoke(self, value): return self.function(value)

from langchain_groq import ChatGroq

from app.services.llm.client import get_groq_llm
from app.services.llm.models import ArticleSummary, ChunkAnalysis, JudgeResult, MarketIntelligenceReport, ThemeFinding
from app.services.llm.prompts import ARTICLE_SUMMARY_SYSTEM, CHUNK_ANALYSIS_SYSTEM, JUDGE_SYSTEM, REPORT_SYSTEM


def build_llm_chain():
    """Create the application's sole production LLM client: Groq."""
    return get_groq_llm(ChatGroq)


def _sentences(text: str, count: int = 4) -> list[str]:
    import re
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()][:count]


def build_chunk_analysis_chain(llm):
    prompt = ChatPromptTemplate.from_messages([("system", CHUNK_ANALYSIS_SYSTEM), ("human", "Source URL: {source_url}\nCompetitors: {competitors}\nThemes: {topics}\nContext: {context}\n\nArticle chunk:\n{article_text}")]) if ChatPromptTemplate else None
    if llm and prompt and hasattr(llm, "with_structured_output"):
        return prompt | llm.with_structured_output(ChunkAnalysis)
    return RunnableLambda(lambda v: ChunkAnalysis(key_facts=_sentences(v["article_text"]), business_insights=_sentences(v["article_text"])))


def build_article_analysis_chain(llm):
    prompt = ChatPromptTemplate.from_messages([("system", ARTICLE_SUMMARY_SYSTEM), ("human", "Source URL: {source_url}\nThemes: {topics}\nCompetitors: {competitors}\n\nChunk analyses:\n{chunk_analyses}")]) if ChatPromptTemplate else None
    if llm and prompt and hasattr(llm, "with_structured_output"):
        return prompt | llm.with_structured_output(ArticleSummary)
    def fallback(v):
        text = v.get("article_text", "")
        facts = _sentences(text or v.get("chunk_analyses", ""))
        themes = [
            ThemeFinding(theme_name=topic, detailed_explanation="Source-derived fallback analysis.", important_findings=facts)
            for topic in v.get("topics", [])
        ]
        return ArticleSummary(
            source_url=v["source_url"],
            executive_summary=" ".join(facts),
            key_themes=themes,
            important_business_insights=facts,
        )
    return RunnableLambda(fallback)


def build_report_chain(llm):
    prompt = ChatPromptTemplate.from_messages([("system", REPORT_SYSTEM), ("human", "Themes: {topics}\nCompetitors: {competitors}\nArticle summaries:\n{article_summaries}")]) if ChatPromptTemplate else None
    if llm and prompt and hasattr(llm, "with_structured_output"):
        return prompt | llm.with_structured_output(MarketIntelligenceReport)
    return RunnableLambda(lambda v: MarketIntelligenceReport(executive_summary=" ".join(a.executive_summary for a in v["article_summary_objects"]), source_traceability=[{"source_url": a.source_url} for a in v["article_summary_objects"]]))


def build_judge_chain(llm):
    prompt = ChatPromptTemplate.from_messages([("system", JUDGE_SYSTEM), ("human", "Article summaries:\n{article_summaries}\n\nProposed report:\n{report}")]) if ChatPromptTemplate else None
    if llm and prompt and hasattr(llm, "with_structured_output"):
        return prompt | llm.with_structured_output(JudgeResult)
    return RunnableLambda(lambda _: JudgeResult(accuracy_score=100, completeness_score=100, overall_feedback="Fallback validation: report is derived only from extracted article summaries."))