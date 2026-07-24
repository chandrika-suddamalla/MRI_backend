from __future__ import annotations

from typing import Any

from app.database.cosmos import CosmosStore, store


class HistoryService:
    """Service for retrieving persisted research reports."""

    def __init__(self, repository: CosmosStore | None = None) -> None:
        self.repository = repository or store

    def _normalize_history_item(self, item: dict[str, Any]) -> dict[str, Any]:
        report = dict(item)
        title = (
            report.get("title")
            or report.get("name")
            or report.get("executiveSummary")
            or report.get("executive_summary")
            or report.get("summary")
            or ""
        )
        if not title and isinstance(report.get("market_intelligence_report"), dict):
            title = report["market_intelligence_report"].get("executive_summary") or ""

        summary = (
            report.get("summary")
            or report.get("executiveSummary")
            or report.get("executive_summary")
            or ""
        )
        if not summary and isinstance(report.get("market_intelligence_report"), dict):
            summary = report["market_intelligence_report"].get("executive_summary") or ""

        competitors = report.get("competitors")
        if not competitors:
            competitor_entries = report.get("competitorActivities") or report.get("competitor_activities") or []
            competitors = []
            for entry in competitor_entries:
                if isinstance(entry, dict):
                    value = entry.get("competitor") or entry.get("name")
                    if value:
                        competitors.append(value)
                elif entry:
                    competitors.append(str(entry))
            if not competitors and isinstance(report.get("market_intelligence_report"), dict):
                competitor_entries = report["market_intelligence_report"].get("competitor_activities") or []
                competitors = []
                for entry in competitor_entries:
                    if isinstance(entry, dict):
                        value = entry.get("competitor") or entry.get("name")
                        if value:
                            competitors.append(value)
                    elif entry:
                        competitors.append(str(entry))

        topics = report.get("topics")
        if not topics:
            theme_entries = report.get("themes") or report.get("key_themes") or []
            topics = []
            for entry in theme_entries:
                if isinstance(entry, dict):
                    value = entry.get("title") or entry.get("name")
                    if value:
                        topics.append(value)
                elif entry:
                    topics.append(str(entry))

        sources = report.get("sources")
        if not sources:
            source_entries = report.get("sourceTraceability") or report.get("source_traceability") or []
            sources = []
            for entry in source_entries:
                if isinstance(entry, dict):
                    value = entry.get("url") or entry.get("title")
                    if value:
                        sources.append(value)
                elif entry:
                    sources.append(str(entry))

        created_at = (
            report.get("created_at")
            or report.get("createdAt")
            or report.get("generated_at")
            or report.get("generatedAt")
            or ""
        )

        report.update(
            {
                "title": title or "Untitled report",
                "summary": summary or "Report generated successfully",
                "created_at": created_at,
                "competitors": competitors or [],
                "topics": topics or [],
                "sources": sources or [],
            }
        )
        return report

    def get_history(self, user_id: str) -> list[dict]:
        return [self._normalize_history_item(item) for item in self.repository.list_reports(user_id)]
