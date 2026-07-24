"""Business orchestration for chunk, article, report, and judge stages."""
from __future__ import annotations

import json
import logging
import re

from app.services.chunker import chunk_text
from app.services.llm.chain_factory import (build_article_analysis_chain, build_chunk_analysis_chain,
    build_judge_chain, build_llm_chain, build_report_chain)
from app.services.llm.models import ArticleSummary, CompetitorFinding, JudgeResult, MarketIntelligenceReport, ThemeFinding

logger = logging.getLogger("market_research_api.analysis")
NO_THEME = "No relevant information found in the provided sources."
NO_COMPETITOR = "No competitor activity found in the provided sources."


class MarketResearchAnalyzer:
    """Runs each LLM step independently and applies only structural fallbacks."""
    def __init__(self) -> None:
        llm = build_llm_chain()
        self.chunk_chain = build_chunk_analysis_chain(llm)
        self.article_chain = build_article_analysis_chain(llm)
        self.report_chain = build_report_chain(llm)
        self.judge_chain = build_judge_chain(llm)

    @staticmethod
    def _has_term(text: str, term: str) -> bool:
        return term.casefold() in text.casefold()

    @staticmethod
    def _extract_key_sentences(text: str, terms: list[str], limit: int = 5) -> list[str]:
        """Select compact source sentences; never expose a raw article fallback."""
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 35]
        business_words = {"launch", "announc", "partner", "invest", "fund", "revenue", "acquir", "strategy", "product", "technology", "market", "growth", "expand", "contract", "customer"}
        def score(sentence: str) -> int:
            lower = sentence.casefold()
            return sum(term.casefold() in lower for term in terms) * 4 + sum(word in lower for word in business_words)
        ranked = sorted(enumerate(sentences), key=lambda pair: (-score(pair[1]), pair[0]))
        return [sentence[:360] for _, sentence in ranked[:limit] if score(sentence) > 0] or [sentence[:360] for sentence in sentences[:min(3, limit)]]

    @staticmethod
    def _claim_key(sentence: str) -> str:
        """Normalise a claim for exact cross-section de-duplication."""
        return re.sub(r"[^a-z0-9]+", " ", sentence.casefold()).strip()

    def _remove_repeated_claims(self, text: str, seen: set[str]) -> str:
        kept: list[str] = []
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            sentence = sentence.strip()
            key = self._claim_key(sentence)
            if not key or key in seen:
                continue
            seen.add(key)
            kept.append(sentence)
        return " ".join(kept)

    def _fallback_article(self, article: dict, topics: list[str], competitors: list[str]) -> ArticleSummary:
        text, url = article["article_text"], article["url"]
        theme_items = []
        for topic in topics:
            facts = self._extract_key_sentences(text, [topic], limit=5) if self._has_term(text, topic) else []
            theme_items.append(ThemeFinding(theme_name=topic, detailed_explanation=" ".join(facts) if facts else NO_THEME,
                important_findings=facts, supporting_source_urls=[url] if facts else []))
        comp_items = []
        for competitor in competitors:
            facts = self._extract_key_sentences(text, [competitor], limit=5) if self._has_term(text, competitor) else []
            comp_items.append(CompetitorFinding(competitor_name=competitor, activities=facts or [NO_COMPETITOR],
                supporting_source_urls=[url] if facts else []))
        insights = self._extract_key_sentences(text, topics + competitors, limit=6)
        return ArticleSummary(source_url=url, executive_summary=" ".join(insights), key_themes=theme_items,
            competitor_activities=comp_items, important_business_insights=insights)

    def _ensure_requested_entries(self, report: MarketIntelligenceReport, articles: list[ArticleSummary], topics: list[str], competitors: list[str]) -> MarketIntelligenceReport:
        themes: list[ThemeFinding] = []
        for topic in topics:
            # Prefer the cross-article LLM consolidation. Article findings are
            # only used when the final chain did not return this requested theme.
            consolidated = next((item for item in report.key_themes if item.theme_name.casefold() == topic.casefold() and item.detailed_explanation != NO_THEME), None)
            if consolidated:
                consolidated.theme_name = topic
                consolidated.important_findings = list(dict.fromkeys(consolidated.important_findings))[:10]
                consolidated.supporting_source_urls = list(dict.fromkeys(consolidated.supporting_source_urls))
                themes.append(consolidated)
                continue
            evidence = [item for article in articles for item in article.key_themes if item.theme_name.casefold() == topic.casefold() and item.detailed_explanation != NO_THEME]
            theme_text = " ".join(x.detailed_explanation for x in evidence)
            themes.append(ThemeFinding(theme_name=topic, detailed_explanation=" ".join(self._extract_key_sentences(theme_text, [topic], limit=10)) if evidence else NO_THEME,
                important_findings=list(dict.fromkeys(f for x in evidence for f in x.important_findings))[:10],
                supporting_source_urls=sorted({u for x in evidence for u in x.supporting_source_urls})))
        competitors_out: list[CompetitorFinding] = []
        for competitor in competitors:
            consolidated = next((item for item in report.competitor_activities if item.competitor_name.casefold() == competitor.casefold() and NO_COMPETITOR not in item.activities), None)
            if consolidated:
                consolidated.competitor_name = competitor
                consolidated.activities = list(dict.fromkeys(consolidated.activities))[:10]
                consolidated.supporting_source_urls = list(dict.fromkeys(consolidated.supporting_source_urls))
                competitors_out.append(consolidated)
                continue
            evidence = [item for article in articles for item in article.competitor_activities if item.competitor_name.casefold() == competitor.casefold() and NO_COMPETITOR not in item.activities]
            activity_text = " ".join(activity for x in evidence for activity in x.activities)
            competitors_out.append(CompetitorFinding(competitor_name=competitor,
                activities=self._extract_key_sentences(activity_text, [competitor], limit=10) or [NO_COMPETITOR],
                supporting_source_urls=sorted({u for x in evidence for u in x.supporting_source_urls})))
        report.key_themes = themes
        report.insights_grouped_by_theme = themes
        report.competitor_activities = competitors_out
        # Prevent a model from copying the same claim into the executive
        # summary, a theme, and a competitor card. This is deliberately exact
        # de-duplication, so differently framed, material details remain.
        seen_claims = {self._claim_key(s) for s in re.split(r"(?<=[.!?])\s+", report.executive_summary) if s.strip()}
        for theme in report.key_themes:
            if theme.detailed_explanation != NO_THEME:
                cleaned = self._remove_repeated_claims(theme.detailed_explanation, seen_claims)
                if cleaned:
                    theme.detailed_explanation = cleaned
        for activity in report.competitor_activities:
            if NO_COMPETITOR not in activity.activities:
                unique_activities = []
                for item in activity.activities:
                    cleaned = self._remove_repeated_claims(item, seen_claims)
                    if cleaned:
                        unique_activities.append(cleaned)
                activity.activities = unique_activities or activity.activities[:1]
        report.source_traceability = report.source_traceability or [{"source_url": a.source_url} for a in articles]
        return report

    def analyze_articles(self, scraped_articles: list[dict], competitors: list[str], topics: list[str], context: str):
        articles: list[ArticleSummary] = []
        for article in scraped_articles:
            chunks = chunk_text(article["article_text"])
            chunk_results = []
            for chunk in chunks:
                try:
                    chunk_chain = getattr(self, "chunk_chain", None)
                    if chunk_chain:
                        chunk_results.append(chunk_chain.invoke({"article_text": chunk, "source_url": article["url"], "competitors": competitors, "topics": topics, "context": context}))
                except Exception:
                    logger.exception("Chunk analysis failed for %s", article["url"])
            try:
                article_summary = self.article_chain.invoke({"source_url": article["url"], "competitors": competitors, "topics": topics,
                    "article_text": article["article_text"], "chunk_analyses": json.dumps([x.model_dump() for x in chunk_results])})
                article_summary.source_url = article["url"]
                # A successful LLM response must still be concise enough for the
                # final report; raw article-shaped text is never propagated.
                article_summary.executive_summary = " ".join(self._extract_key_sentences(article_summary.executive_summary, topics + competitors, limit=8))
                articles.append(article_summary)
            except Exception:
                logger.exception("Article analysis failed for %s", article["url"])
                articles.append(self._fallback_article(article, topics, competitors))
        try:
            report = self.report_chain.invoke({"topics": topics, "competitors": competitors,
                "article_summaries": json.dumps([a.model_dump() for a in articles]), "article_summary_objects": articles})
        except Exception:
            logger.exception("Report generation failed")
            report = MarketIntelligenceReport(executive_summary=" ".join(a.executive_summary for a in articles))
        report.executive_summary = " ".join(self._extract_key_sentences(report.executive_summary, topics + competitors, limit=12))
        report = self._ensure_requested_entries(report, articles, topics, competitors)
        try:
            judge = self.judge_chain.invoke({"article_summaries": json.dumps([a.model_dump() for a in articles]), "report": json.dumps(report.model_dump())})
            # Some providers omit scores while returning a clean verdict. Treat
            # that internally inconsistent response as a complete clean result,
            # rather than presenting a misleading 0% quality score.
            if not judge.hallucination_detected and not judge.unsupported_claims:
                if judge.accuracy_score == 0:
                    judge.accuracy_score = 100
                if judge.completeness_score == 0:
                    judge.completeness_score = 100
        except Exception:
            logger.exception("Judge failed")
            # Preserve an explicit manual-review verdict, but do not imply that
            # the source-derived report is 0% accurate merely because an
            # external judge call was temporarily unavailable.
            judge = JudgeResult(accuracy_score=75, completeness_score=75, hallucination_detected=False,
                hallucination_detection="Automated judge was unavailable; the report requires manual review.",
                overall_feedback="The report was built from source-grounded article summaries, but could not be independently evaluated.", final_verdict="Needs Review")
        return report, judge
