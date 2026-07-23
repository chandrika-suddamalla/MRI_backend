from __future__ import annotations

import logging
from typing import Any

from app.schemas.research import (
    CompetitorActivityOut,
    HallucinationCheckOut,
    ResearchRequest,
    ResearchResponse,
    ThemeOut,
)
from app.services.analysis import MarketResearchAnalyzer
from app.services.scraper import ArticleScraper

logger = logging.getLogger("market_research_api")


class ResearchService:
    """Service containing research workflow business logic."""

    def __init__(self) -> None:
        self.scraper = ArticleScraper()
        self.analyzer = MarketResearchAnalyzer()

    def create_research(self, payload: ResearchRequest) -> ResearchResponse:
        """Scrape, analyze, and merge article content into a structured report."""
        logger.info(
            "Research request received with competitors=%s topics=%s urls=%s context=%s",
            payload.competitors,
            payload.topics,
            payload.urls,
            payload.context,
        )

        scraped_articles = self.scraper.scrape_articles(payload.urls)
        report, judge_result = self.analyzer.analyze_articles(
            scraped_articles=scraped_articles,
            competitors=payload.competitors,
            topics=payload.topics,
            context=payload.context,
        )

        topic_sections = self._build_topic_sections(report, payload)
        themes = [
            ThemeOut(
                title=item.get("theme", "Research theme"),
                summary=item.get("summary", "No summary available"),
                sources=list(item.get("sources", [])),
            )
            for item in topic_sections
        ]
        competitor_sections = self._build_competitor_sections(report, payload)
        competitor_activities = [
            CompetitorActivityOut(
                competitor=item.get("competitor", "Reported competitor"),
                activity=item.get("activity", "No activity available"),
                sources=list(item.get("sources", [])),
            )
            for item in competitor_sections
        ]
        if not themes or any(theme.title in {"Research summary", "Research themes"} for theme in themes):
            theme_title = self._derive_theme_title(payload)
            themes = [ThemeOut(title=theme_title, summary=report.executive_summary or "The provided source could not be parsed into a usable article summary. Please try another URL.", sources=[source.get("source_url") for source in report.source_traceability if isinstance(source, dict) and source.get("source_url")])]
        hallucination_check = HallucinationCheckOut(
            status="Supported" if judge_result.hallucination_detection and "unsupported" not in judge_result.hallucination_detection.lower() else "Needs review",
            confidence=float(judge_result.accuracy_score),
            accuracy_score=float(judge_result.accuracy_score),
            completeness_score=float(judge_result.completeness_score),
            unsupported_claims=list(judge_result.unsupported_claims or []),
            overall_feedback=judge_result.overall_feedback or "",
        )

        return ResearchResponse(
            executiveSummary=report.executive_summary or "",
            themes=themes,
            marketTrends=list(report.market_trends or []),
            competitorActivities=competitor_activities,
            businessInsights=list(report.business_insights or []),
            statistics=list(report.statistics or []),
            companiesMentioned=list(report.companies_mentioned or []),
            sourceTraceability=list(report.source_traceability or []),
            hallucinationCheck=hallucination_check,
        )

    def _derive_theme_title(self, payload: ResearchRequest) -> str:
        tokens = [*payload.competitors, *payload.topics]
        if not tokens:
            return "Research summary"
        combined = ", ".join(tokens[:3])
        return combined if len(tokens) <= 3 else f"{combined}..."

    def _build_theme_sections(self, report: Any) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        for item in report.insights_grouped_by_theme:
            if isinstance(item, dict):
                theme_name = item.get("theme") or item.get("title") or "Research theme"
                summary = item.get("summary") or "No summary available"
                sources = list(item.get("sources", []))
                sections.append({"theme": theme_name, "summary": summary, "sources": sources})
        if not sections:
            sections.append({
                "theme": "Research summary",
                "summary": report.executive_summary,
                "sources": [source.get("source_url") for source in report.source_traceability if isinstance(source, dict) and source.get("source_url")],
            })
        return sections

    def _build_topic_sections(self, report: Any, payload: ResearchRequest) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        theme_sections = self._build_theme_sections(report)
        if theme_sections:
            sections.extend(theme_sections)
        if payload.topics:
            requested_topics = [topic.strip() for topic in payload.topics if topic and topic.strip()]
            if requested_topics:
                final_sections: list[dict[str, Any]] = []
                seen_themes: set[str] = set()
                for topic in requested_topics:
                    matched = False
                    for section in sections:
                        theme_name = str(section.get("theme", "")).lower()
                        if topic.lower() in theme_name or theme_name.startswith(topic.lower()):
                            matched = True
                            if theme_name not in seen_themes:
                                final_sections.append(section)
                                seen_themes.add(theme_name)
                    if not matched:
                        final_sections.append({
                            "theme": topic,
                            "summary": "No information found for this topic in the provided sources.",
                            "sources": [],
                        })
                if final_sections:
                    return final_sections
        return sections

    def _build_competitor_sections(self, report: Any, payload: ResearchRequest) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        sources = [source.get("source_url") for source in report.source_traceability if isinstance(source, dict) and source.get("source_url")]
        for competitor in payload.competitors:
            competitor_name = competitor.strip()
            activities = [activity for activity in report.competitor_activities if isinstance(activity, str) and competitor_name.lower() in activity.lower()]
            if activities:
                sections.append({
                    "competitor": competitor_name,
                    "activity": " ".join(activities),
                    "sources": sources,
                })
            else:
                sections.append({
                    "competitor": competitor_name,
                    "activity": "No competitor activity found in the provided sources.",
                    "sources": sources,
                })

        if not sections and report.source_traceability:
            competitor_name = payload.competitors[0] if payload.competitors else "Reported competitor"
            sections.append({
                "competitor": competitor_name,
                "activity": report.executive_summary,
                "sources": [source.get("source_url") for source in report.source_traceability if isinstance(source, dict) and source.get("source_url")],
            })
        return sections
