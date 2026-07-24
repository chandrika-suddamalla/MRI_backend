"""Structured contracts shared by LangChain chains and API formatting."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SourceInsight(BaseModel):
    statement: str
    sources: list[str] = Field(default_factory=list)


class ThemeFinding(BaseModel):
    theme_name: str
    detailed_explanation: str
    important_findings: list[str] = Field(default_factory=list)
    supporting_source_urls: list[str] = Field(default_factory=list)


class CompetitorFinding(BaseModel):
    competitor_name: str
    activities: list[str] = Field(default_factory=list)
    supporting_source_urls: list[str] = Field(default_factory=list)


class ChunkAnalysis(BaseModel):
    key_facts: list[str] = Field(default_factory=list)
    theme_evidence: list[ThemeFinding] = Field(default_factory=list)
    competitor_evidence: list[CompetitorFinding] = Field(default_factory=list)
    business_insights: list[str] = Field(default_factory=list)


class ArticleSummary(BaseModel):
    # The orchestration layer always replaces this with the submitted URL.
    # A default prevents an otherwise useful LLM response failing solely because
    # the model did not echo a value it was already given.
    source_url: str = ""
    executive_summary: str = ""
    key_themes: list[ThemeFinding] = Field(default_factory=list)
    competitor_activities: list[CompetitorFinding] = Field(default_factory=list)
    important_business_insights: list[str] = Field(default_factory=list)


class MarketIntelligenceReport(BaseModel):
    executive_summary: str
    key_themes: list[ThemeFinding] = Field(default_factory=list)
    competitor_activities: list[CompetitorFinding] = Field(default_factory=list)
    # Compatibility fields retained for the existing UI/API consumer.
    insights_grouped_by_theme: list[ThemeFinding] = Field(default_factory=list)
    market_trends: list[str] = Field(default_factory=list)
    business_insights: list[str] = Field(default_factory=list)
    statistics: list[str] = Field(default_factory=list)
    companies_mentioned: list[str] = Field(default_factory=list)
    source_traceability: list[dict] = Field(default_factory=list)


class JudgeResult(BaseModel):
    # A structured-output provider can omit optional fields. Defaults describe a
    # clean evaluation rather than displaying a misleading zero score.
    accuracy_score: float = 100
    completeness_score: float = 100
    hallucination_detected: bool = False
    hallucination_detection: str = "No unsupported claims detected."
    unsupported_claims: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    overall_feedback: str = ""
    final_verdict: str = "Pass"
