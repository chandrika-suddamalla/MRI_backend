from __future__ import annotations

from typing import Any, List
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    """Incoming research request payload."""

    competitors: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)
    context: str = ""


class ThemeOut(BaseModel):
    """A research theme included in the mock report."""

    title: str
    summary: str
    sources: List[str] = Field(default_factory=list)


class CompetitorActivityOut(BaseModel):
    """Competitor activity summary."""

    competitor: str
    activity: str
    sources: List[str] = Field(default_factory=list)


class HallucinationCheckOut(BaseModel):
    """Hallucination check section of the report."""

    status: str
    confidence: float
    accuracy_score: float = 0.0
    completeness_score: float = 0.0
    unsupported_claims: List[str] = Field(default_factory=list)
    overall_feedback: str = ""


class ResearchResponse(BaseModel):
    """Structured market intelligence report response."""

    executiveSummary: str = ""
    themes: List[ThemeOut] = Field(default_factory=list)
    marketTrends: List[str] = Field(default_factory=list)
    competitorActivities: List[CompetitorActivityOut] = Field(default_factory=list)
    businessInsights: List[str] = Field(default_factory=list)
    statistics: List[str] = Field(default_factory=list)
    companiesMentioned: List[str] = Field(default_factory=list)
    sourceTraceability: List[dict[str, Any]] = Field(default_factory=list)
    hallucinationCheck: HallucinationCheckOut
