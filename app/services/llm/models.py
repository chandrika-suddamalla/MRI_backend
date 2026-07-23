from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ArticleAnalysis(BaseModel):
    """Structured analysis for a single article."""

    source_url: str = Field(..., description="The URL of the source article")
    executive_summary: str = Field(..., description="Short summary of the article")
    key_themes: List[str] = Field(default_factory=list, description="Key themes or trends from the article")
    competitor_activities: List[str] = Field(default_factory=list, description="Competitor activities mentioned")
    business_insights: List[str] = Field(default_factory=list, description="Business insights from the article")
    statistics: List[str] = Field(default_factory=list, description="Statistics or quantitative facts from the article")
    companies_organizations: List[str] = Field(default_factory=list, description="Organizations mentioned in the article")


class ArticleAnalysisList(BaseModel):
    """Collection of article analyses."""

    analyses: List[ArticleAnalysis] = Field(default_factory=list)


class MarketIntelligenceReport(BaseModel):
    """Consolidated market intelligence report."""

    executive_summary: str = Field(..., description="Executive summary of the whole report")
    insights_grouped_by_theme: List[dict[str, object]] = Field(default_factory=list)
    market_trends: List[str] = Field(default_factory=list)
    competitor_activities: List[str] = Field(default_factory=list)
    business_insights: List[str] = Field(default_factory=list)
    statistics: List[str] = Field(default_factory=list)
    companies_mentioned: List[str] = Field(default_factory=list)
    source_traceability: List[dict[str, object]] = Field(default_factory=list)


class JudgeResult(BaseModel):
    """Validation result from the judge chain."""

    accuracy_score: float = Field(..., ge=0, le=1)
    completeness_score: float = Field(..., ge=0, le=1)
    hallucination_detection: str = Field(...)
    unsupported_claims: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    overall_feedback: str = Field(...)
