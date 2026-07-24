"""API-facing research workflow: extraction, analysis, and response formatting."""
from __future__ import annotations

import logging
from fastapi import HTTPException, status

from app.database.cosmos import CosmosStore, store
from app.schemas.research import CompetitorActivityOut, HallucinationCheckOut, ResearchRequest, ResearchResponse, ThemeOut
from app.services.analysis import MarketResearchAnalyzer, NO_COMPETITOR, NO_THEME
from app.services.scraper import SourceExtractionError, TrafilaturaScraper

logger = logging.getLogger("market_research_api.research")


class ResearchService:
    def __init__(self, scraper: TrafilaturaScraper | None = None, analyzer: MarketResearchAnalyzer | None = None,
                 repository: CosmosStore | None = None) -> None:
        self.scraper = scraper or TrafilaturaScraper()
        self.analyzer = analyzer or MarketResearchAnalyzer()
        self.repository = repository or store

    def create_research(self, payload: ResearchRequest, user_id: str | None = None) -> ResearchResponse:
        articles, failures = [], []
        # Keep individual extraction errors visible while allowing useful sources to proceed.
        for url in payload.urls:
            try:
                articles.extend(self.scraper.scrape_articles([str(url)]))
            except SourceExtractionError as exc:
                failures.append({"url": str(url), "status": "failed", "error": str(exc)})
        if not articles:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"message": "None of the submitted URLs could be extracted.", "sources": failures})

        report, judge = self.analyzer.analyze_articles(articles, payload.competitors, payload.topics, payload.context)
        themes = [ThemeOut(title=item.theme_name, summary=item.detailed_explanation or NO_THEME,
            sources=item.supporting_source_urls) for item in report.key_themes]
        activities = [CompetitorActivityOut(competitor=item.competitor_name,
            activity="\n".join(item.activities) or NO_COMPETITOR, sources=item.supporting_source_urls)
            for item in report.competitor_activities]
        # A report must explicitly account for every requested entity, even when a
        # custom analyzer or an LLM returns no matching object.
        known_themes = {item.title.casefold() for item in themes}
        themes.extend(ThemeOut(title=topic, summary=f"{NO_THEME} No information found for this topic in the provided sources.", sources=[])
                      for topic in payload.topics if topic.casefold() not in known_themes)
        known_competitors = {item.competitor.casefold() for item in activities}
        activities.extend(CompetitorActivityOut(competitor=name, activity=NO_COMPETITOR, sources=[])
                          for name in payload.competitors if name.casefold() not in known_competitors)
        traceability = [{"url": article["url"], "title": article.get("title") or "Untitled source", "status": "extracted",
                          "characters_extracted": len(article["article_text"])} for article in articles] + failures
        judge_payload = judge.model_dump()
        response = ResearchResponse(
            executiveSummary=report.executive_summary,
            themes=themes,
            competitorActivities=activities,
            marketTrends=report.market_trends,
            businessInsights=report.business_insights,
            statistics=report.statistics,
            companiesMentioned=report.companies_mentioned,
            sourceTraceability=traceability,
            hallucinationCheck=HallucinationCheckOut(
                status="Supported" if judge.final_verdict.casefold() == "pass" else "Needs review",
                confidence=judge.accuracy_score / 100,
                accuracy_score=judge.accuracy_score / 100,
                completeness_score=judge.completeness_score / 100,
                hallucination_detected=judge.hallucination_detected,
                unsupported_claims=judge.unsupported_claims,
                missing_information=judge.missing_information,
                overall_feedback=judge.overall_feedback,
                final_verdict=judge.final_verdict,
            ),
            market_intelligence_report={
                "executive_summary": report.executive_summary,
                "key_themes": [item.model_dump() for item in report.key_themes],
                "competitor_activities": [item.model_dump() for item in report.competitor_activities],
            },
            llm_judge_result=judge_payload,
        )
        if user_id:
            history_payload = response.model_dump()
            history_payload.update(
                {
                    "title": response.executiveSummary or "Untitled report",
                    "summary": response.executiveSummary or "Report generated successfully",
                    "competitors": [item.competitor for item in response.competitorActivities],
                    "topics": [item.title for item in response.themes],
                    "sources": [item.get("url") for item in traceability if isinstance(item, dict) and item.get("url")],
                }
            )
            self.repository.save_report(str(user_id), history_payload)
        return response
