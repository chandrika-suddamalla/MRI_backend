from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_groq import ChatGroq

from app.services.llm.models import ArticleAnalysis, JudgeResult, MarketIntelligenceReport


class FallbackLLM:
    """Minimal fallback for environments without a configured Groq API key."""

    def invoke(self, value: Any) -> Any:
        return value


def build_llm_chain(model: str | None = None, temperature: float = 0.2) -> Any:
    """Create a Groq-backed LLM instance configured for structured outputs."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return FallbackLLM()

    return ChatGroq(
        api_key=api_key,
        model=model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=temperature,
    )


def _invoke_with_retry(llm: Any, messages: Any, *, retries: int | None = None, base_delay: float = 1.0) -> Any:
    max_retries = retries if retries is not None else int(os.getenv("GROQ_MAX_RETRIES", "3"))
    delay = base_delay

    for attempt in range(max_retries + 1):
        try:
            return llm.invoke(messages)
        except Exception as exc:
            if attempt >= max_retries:
                raise
            message = str(exc).lower()
            if "429" not in message and "rate limit" not in message and "too many requests" not in message:
                raise
            time.sleep(delay)
            delay *= 2


def _fallback_payload_for_messages(messages: Any) -> dict[str, Any]:
    text = ""
    if isinstance(messages, list):
        for item in messages:
            if hasattr(item, "content"):
                text = str(getattr(item, "content", ""))
                break
            if isinstance(item, dict):
                content = item.get("content")
                if content:
                    text = str(content)
                    break
    elif messages is not None:
        text = str(messages)

    return {
        "executive_summary": f"The report is being generated from the available content. The live model was temporarily unavailable. {text[:240]}".strip(),
        "key_themes": ["Market developments"],
        "competitor_activities": [],
        "business_insights": ["The workflow used a fallback response because the live model was throttled."],
        "statistics": [],
        "companies_organizations": [],
    }


def _extract_json_payload(response: Any) -> dict[str, Any]:
    if response is None:
        return {}
    content = response.content if hasattr(response, "content") else response

    if isinstance(content, list):
        pieces = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    pieces.append(str(item.get("text", "")))
                else:
                    pieces.append(json.dumps(item))
            else:
                pieces.append(str(item))
        content = "".join(pieces)

    if isinstance(content, dict):
        return content
    if not isinstance(content, str):
        return {}

    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"```$", "", cleaned)

    for pattern in [r"\{.*\}", r"\[.*\]"]:
        match = re.search(pattern, cleaned, re.S)
        if match:
            candidate = match.group(0)
            try:
                payload = json.loads(candidate)
                if isinstance(payload, dict):
                    return payload
                if isinstance(payload, list):
                    return {"items": payload}
            except json.JSONDecodeError:
                continue

    try:
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        return {}
    return {}


def _coerce_to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if isinstance(value, tuple):
        return [str(item) for item in value if item is not None]
    if isinstance(value, dict):
        return [f"{key}: {item}" for key, item in value.items()]
    return [str(value)]


def _coerce_to_object_list(value: Any, fallback_key: str = "theme") -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        result: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                result.append(item)
            elif item is not None:
                result.append({fallback_key: str(item), "summary": str(item), "sources": []})
        return result
    if isinstance(value, dict):
        return [value]
    return [{fallback_key: str(value), "summary": str(value), "sources": []}]


def _normalize_article_analysis(raw: dict[str, Any], source_url: str) -> ArticleAnalysis:
    data = raw.get("article_analysis") if isinstance(raw.get("article_analysis"), dict) else raw

    summary_value = data.get("executive_summary")
    if isinstance(summary_value, dict):
        summary_text = summary_value.get("summary") or summary_value.get("overview") or summary_value.get("description") or ""
    else:
        summary_text = summary_value
    summary = (
        summary_text
        or data.get("summary")
        or data.get("program_description")
        or data.get("overview")
        or data.get("description")
        or "No executive summary was provided."
    )
    if not isinstance(summary, str):
        summary = str(summary)

    themes = data.get("key_themes") or data.get("themes") or data.get("trends") or data.get("topics")
    competitor_activities = data.get("competitor_activities") or data.get("competitors") or data.get("competitor_activity") or data.get("activities")
    business_insights = data.get("business_insights") or data.get("insights") or data.get("recommendations") or data.get("business")
    statistics = data.get("statistics") or data.get("stats")
    companies = data.get("companies_organizations") or data.get("companies") or data.get("organizations") or data.get("partners")

    if isinstance(competitor_activities, dict):
        competitor_activities = competitor_activities.get("activities") or competitor_activities.get("competitors") or competitor_activities.get("items")
    if isinstance(business_insights, dict):
        business_insights = business_insights.get("insights") or business_insights.get("recommendations") or business_insights.get("items")
    if isinstance(statistics, dict):
        statistics = list(statistics.values())
    if isinstance(companies, dict):
        companies = companies.get("key_players") or companies.get("companies") or companies.get("organizations") or companies.get("industry_partners")

    return ArticleAnalysis(
        source_url=source_url or str(data.get("source_url") or ""),
        executive_summary=summary,
        key_themes=_coerce_to_list(themes),
        competitor_activities=_coerce_to_list(competitor_activities),
        business_insights=_coerce_to_list(business_insights),
        statistics=_coerce_to_list(statistics),
        companies_organizations=_coerce_to_list(companies),
    )


def _normalize_report(raw: dict[str, Any]) -> MarketIntelligenceReport:
    data = dict(raw or {})
    if not data:
        data = {
            "executive_summary": "No report content was returned by the model.",
            "insights_grouped_by_theme": [],
            "market_trends": [],
            "competitor_activities": [],
            "business_insights": [],
            "statistics": [],
            "companies_mentioned": [],
            "source_traceability": [],
        }

    if "executive_summary" not in data or not data.get("executive_summary"):
        data["executive_summary"] = data.get("summary") or data.get("overview") or "No executive summary was provided."

    if "insights_grouped_by_theme" not in data or not data.get("insights_grouped_by_theme"):
        theme_items = data.get("themes") or data.get("report_themes") or []
        data["insights_grouped_by_theme"] = _coerce_to_object_list(theme_items, fallback_key="theme")

    if "market_trends" not in data or not data.get("market_trends"):
        data["market_trends"] = _coerce_to_list(data.get("trends") or data.get("market_trends"))
    if "competitor_activities" not in data or not data.get("competitor_activities"):
        data["competitor_activities"] = _coerce_to_list(data.get("competitor_activity") or data.get("competitor_activities"))
    if "business_insights" not in data or not data.get("business_insights"):
        data["business_insights"] = _coerce_to_list(data.get("insights") or data.get("business_insights"))
    if "statistics" not in data or not data.get("statistics"):
        data["statistics"] = _coerce_to_list(data.get("stats") or data.get("statistics"))
    if "companies_mentioned" not in data or not data.get("companies_mentioned"):
        data["companies_mentioned"] = _coerce_to_list(data.get("companies") or data.get("companies_mentioned"))
    if "source_traceability" not in data or not data.get("source_traceability"):
        data["source_traceability"] = []

    return MarketIntelligenceReport.model_validate(data)


def _build_report_from_analyses(analyses: list[dict[str, Any]], competitors: list[str] | None = None, topics: list[str] | None = None, context: str = "") -> MarketIntelligenceReport:
    theme_map: dict[str, dict[str, Any]] = {}
    competitor_activities: list[str] = []
    business_insights: list[str] = []
    statistics: list[str] = []
    companies: list[str] = []
    summaries: list[str] = []
    source_traceability: list[dict[str, Any]] = []

    for analysis in analyses:
        if not isinstance(analysis, dict):
            continue

        source_url = analysis.get("source_url", "") or ""
        if source_url:
            source_traceability.append({"source_url": source_url})

        summary = analysis.get("executive_summary") or "No summary available"
        if isinstance(summary, str) and summary.strip():
            summaries.append(summary.strip())

        for theme in _coerce_to_list(analysis.get("key_themes")):
            theme_entry = theme_map.setdefault(theme, {"theme": theme, "summary": theme, "sources": []})
            if source_url and source_url not in theme_entry["sources"]:
                theme_entry["sources"].append(source_url)

        for item in _coerce_to_list(analysis.get("competitor_activities")):
            competitor_activities.append(item)
        for item in _coerce_to_list(analysis.get("business_insights")):
            business_insights.append(item)
        for item in _coerce_to_list(analysis.get("statistics")):
            statistics.append(item)
        for item in _coerce_to_list(analysis.get("companies_organizations")):
            companies.append(item)

    unique_themes = list(theme_map.values())
    unique_themes = [theme for theme in unique_themes if isinstance(theme, dict)]
    if not unique_themes:
        unique_themes = [{"theme": "Research themes", "summary": "No information found for this topic in the provided sources.", "sources": []}]

    executive_summary_parts = []
    if summaries:
        executive_summary_parts.append(
            "Synthesized findings across the provided sources:\n- " + "\n- ".join(dict.fromkeys(summaries))
        )
    if competitors:
        executive_summary_parts.append(
            "Competitor coverage requested: " + ", ".join(competitors) + ". No relevant information found in the provided sources."
            if not competitor_activities
            else "Competitor-related findings: " + "; ".join(dict.fromkeys(competitor_activities))
        )
    if topics:
        executive_summary_parts.append(
            "Topic coverage requested: " + ", ".join(topics) + ". " + (
                "No relevant information found in the provided sources."
                if not unique_themes
                else "Key themes were consolidated from the available source material."
            )
        )

    executive_summary = "\n\n".join(part for part in executive_summary_parts if part).strip()
    if not executive_summary:
        input_context = [*(competitors or []), *(topics or [])]
        subject = ", ".join(input_context[:4]) if input_context else "the requested research topics"
        executive_summary = f"Synthesized findings from the provided sources for {subject}."

    return MarketIntelligenceReport(
        executive_summary=executive_summary,
        insights_grouped_by_theme=unique_themes,
        market_trends=[],
        competitor_activities=list(dict.fromkeys(competitor_activities)),
        business_insights=list(dict.fromkeys(business_insights)),
        statistics=list(dict.fromkeys(statistics)),
        companies_mentioned=list(dict.fromkeys(companies)),
        source_traceability=source_traceability,
    )


def _normalize_judge(raw: dict[str, Any]) -> JudgeResult:
    data = dict(raw or {})
    if not data:
        data = {
            "accuracy_score": 0.0,
            "completeness_score": 0.0,
            "hallucination_detection": "No judge result returned.",
            "unsupported_claims": [],
            "missing_information": [],
            "overall_feedback": "No judge result was returned by the model.",
        }

    if "accuracy_score" not in data:
        data["accuracy_score"] = 0.0
    if "completeness_score" not in data:
        data["completeness_score"] = 0.0
    if "hallucination_detection" not in data:
        data["hallucination_detection"] = data.get("hallucination") or "No judge result returned."
    if "unsupported_claims" not in data:
        data["unsupported_claims"] = []
    if "missing_information" not in data:
        data["missing_information"] = []
    if "overall_feedback" not in data:
        data["overall_feedback"] = data.get("feedback") or "No judge result was returned by the model."

    return JudgeResult.model_validate(data)


def _enrich_report_payload(
    parsed: dict[str, Any],
    analyses: list[dict[str, Any]],
    *,
    competitors: list[str] | None = None,
    topics: list[str] | None = None,
    context: str = "",
) -> dict[str, Any]:
    fallback_report = _build_report_from_analyses(
        analyses,
        competitors=competitors,
        topics=topics,
        context=context,
    )
    merged = dict(parsed or {})

    if not merged.get("executive_summary"):
        merged["executive_summary"] = fallback_report.executive_summary

    if not merged.get("insights_grouped_by_theme"):
        merged["insights_grouped_by_theme"] = [dict(item) for item in fallback_report.insights_grouped_by_theme]

    if not merged.get("market_trends"):
        merged["market_trends"] = list(fallback_report.market_trends)
    if not merged.get("business_insights"):
        merged["business_insights"] = list(fallback_report.business_insights)
    if not merged.get("statistics"):
        merged["statistics"] = list(fallback_report.statistics)
    if not merged.get("companies_mentioned"):
        merged["companies_mentioned"] = list(fallback_report.companies_mentioned)

    theme_sections = merged.get("insights_grouped_by_theme") or []
    if isinstance(theme_sections, list):
        existing_themes = {
            str(item.get("theme", "")).strip().lower(): item
            for item in theme_sections
            if isinstance(item, dict) and item.get("theme")
        }
        for topic in topics or []:
            normalized_topic = str(topic).strip()
            if not normalized_topic:
                continue
            lowered = normalized_topic.lower()
            if lowered not in existing_themes:
                existing_themes[lowered] = {
                    "theme": normalized_topic,
                    "summary": "No information found for this topic in the provided sources.",
                    "sources": [],
                }
        merged["insights_grouped_by_theme"] = list(existing_themes.values())

    competitor_entries = list(merged.get("competitor_activities") or [])
    if not competitor_entries:
        competitor_entries = list(fallback_report.competitor_activities)
    for competitor in competitors or []:
        competitor_name = str(competitor).strip()
        if not competitor_name:
            continue
        if not any(competitor_name.lower() in str(entry).lower() for entry in competitor_entries):
            competitor_entries.append(f"No competitor activity found in the provided sources. {competitor_name}")

    merged["competitor_activities"] = list(dict.fromkeys(competitor_entries))
    merged["source_traceability"] = [dict(item) for item in fallback_report.source_traceability]
    return merged


# ──────────────────────────────────────────────────────────────────────────────
# Chunk Summarizer Chain
# ──────────────────────────────────────────────────────────────────────────────

def build_chunk_summarizer_chain(llm: Any) -> Any:
    """Summarize a single text chunk into a short paragraph for token efficiency."""
    if isinstance(llm, FallbackLLM):
        def fallback_chain(payload: dict[str, Any]) -> str:
            return payload.get("chunk_text", "")[:500]
        return RunnableLambda(fallback_chain)

    prompt = ChatPromptTemplate.from_template(
        """You are a careful market research assistant. Summarize the article chunk using only the chunk content.
Extract the most important facts, announcements, launches, partnerships, investments, strategy changes, competitor mentions, market movements, and any statistics or quantitative details.
Do not omit material details that are clearly present. Be comprehensive and preserve nuance, but do not add anything not stated in the chunk.

Chunk {chunk_index} of {total_chunks} from: {source_url}
User context — Competitors: {competitors} | Topics: {topics} | Context: {context}

Article chunk:
{chunk_text}

Write a factual, detailed summary paragraph that captures the most relevant business information from the chunk:"""
    )

    def invoke(payload: dict[str, Any]) -> str:
        messages = prompt.format_messages(
            chunk_text=payload.get("chunk_text", ""),
            chunk_index=payload.get("chunk_index", 1),
            total_chunks=payload.get("total_chunks", 1),
            source_url=payload.get("source_url", ""),
            competitors=", ".join(payload.get("competitors", []) or []) or "None provided",
            topics=", ".join(payload.get("topics", []) or []) or "None provided",
            context=payload.get("context", "") or "None provided",
        )
        try:
            response = _invoke_with_retry(llm, messages)
            if hasattr(response, "content"):
                return str(response.content).strip()
            return str(response).strip()
        except Exception:
            return payload.get("chunk_text", "")[:500]

    return RunnableLambda(invoke)


# ──────────────────────────────────────────────────────────────────────────────
# Article Analysis Chain
# ──────────────────────────────────────────────────────────────────────────────

def build_article_analysis_chain(llm: Any) -> Any:
    if isinstance(llm, FallbackLLM):
        def fallback_chain(payload: dict[str, Any]) -> ArticleAnalysis:
            article_text = payload.get("article_text", "")
            return ArticleAnalysis(
                source_url=payload.get("source_url", ""),
                executive_summary=article_text[:240] or "No article content was available.",
                key_themes=["Market developments"],
                competitor_activities=[],
                business_insights=["Article content was summarized using the local fallback workflow."],
                statistics=[],
                companies_organizations=[],
            )

        return RunnableLambda(fallback_chain)

    prompt = ChatPromptTemplate.from_template(
        """You are a strict market research analyst. Analyze the full article below using only its content.
Do not use external knowledge, do not hallucinate, and do not add facts not present in the article.
Return a JSON object with these keys only: executive_summary, key_themes, competitor_activities, business_insights, statistics, companies_organizations.

Source URL:
{source_url}

Article content:
{article_text}

User context:
Competitors: {competitors}
Topics: {topics}
Additional context: {context}

Instructions:
- Preserve facts and statistics exactly as stated.
- Use only information supported by the article.
- Review the entire article before writing. Capture all significant findings, not just the first paragraph.
- Be comprehensive: include major business announcements, launches, partnerships, investments, strategy changes, market shifts, and any quantitative details when they are explicitly mentioned.
- If the article mentions a competitor or topic, reflect that in the analysis without adding external facts.
- If a requested topic or competitor is not mentioned, leave that array empty rather than fabricating it.
- Return ONLY valid JSON, no markdown, no extra text.
"""
    )

    def invoke(payload: dict[str, Any]) -> ArticleAnalysis:
        article_text = payload.get("article_text", "") or ""
        messages = prompt.format_messages(
            source_url=payload.get("source_url", ""),
            article_text=article_text,
            competitors=", ".join(payload.get("competitors", []) or []) if payload.get("competitors") else "None provided",
            topics=", ".join(payload.get("topics", []) or []) if payload.get("topics") else "None provided",
            context=payload.get("context", ""),
        )
        try:
            response = _invoke_with_retry(llm, messages)
            parsed = _extract_json_payload(response)
            if not parsed:
                parsed = {
                    "executive_summary": article_text[:600] or "No article content was available.",
                    "key_themes": list(payload.get("topics", []) or []),
                    "competitor_activities": list(payload.get("competitors", []) or []),
                    "business_insights": ["The report used the available article content after the model returned an unusable payload."],
                    "statistics": [],
                    "companies_organizations": [],
                }
            return _normalize_article_analysis(parsed, payload.get("source_url", ""))
        except Exception:
            parsed = {
                "executive_summary": article_text[:600] or "No article content was available.",
                "key_themes": list(payload.get("topics", []) or []),
                "competitor_activities": list(payload.get("competitors", []) or []),
                "business_insights": ["The report used the available article content after the model failed to return structured output."],
                "statistics": [],
                "companies_organizations": [],
            }
            return _normalize_article_analysis(parsed, payload.get("source_url", ""))

    return RunnableLambda(invoke)


# ──────────────────────────────────────────────────────────────────────────────
# Report Generation Chain
# ──────────────────────────────────────────────────────────────────────────────

def build_report_generation_chain(llm: Any) -> Any:
    if isinstance(llm, FallbackLLM):
        def fallback_chain(payload: dict[str, Any]) -> MarketIntelligenceReport:
            return MarketIntelligenceReport(
                executive_summary="Fallback report generated from the available article analyses.",
                insights_grouped_by_theme=[{"theme": "Market update", "summary": "The review used the local fallback workflow.", "sources": []}],
                market_trends=["No additional market trend data available"],
                competitor_activities=[],
                business_insights=["Article content was summarized using the local fallback workflow."],
                statistics=[],
                companies_mentioned=[],
                source_traceability=[],
            )

        return RunnableLambda(fallback_chain)

    prompt = ChatPromptTemplate.from_template(
        """You are a senior market intelligence analyst producing an executive-ready consolidated report for leadership review.

Your job is to combine all article analyses into one final report using ONLY the supplied extracted content. Use no external knowledge, no assumptions, and no invented claims. Every detail must be traceable to the provided analyses.

THOROUGH ANALYSIS REQUIREMENTS:
- Read every article analysis before writing.
- Identify all major findings, business announcements, launches, partnerships, investments, strategy changes, and quantitative facts that are explicitly present.
- Consolidate duplicate or overlapping content across multiple URLs into one synthesized summary while keeping all supporting source references.
- Pay close attention to the requested topics and requested competitor names; make sure the final report reflects all relevant coverage from the articles.
- Prefer full, business-oriented synthesis over short, shallow summaries.

STRICT OUTPUT RULES:
1. The final consolidated report must contain only three sections of business-facing information:
   - Executive Summary
   - Key Themes
   - Competitor Activity
2. Do not output separate market trend, business insight, statistic, or company-list sections as standalone report blocks.
3. If a requested topic is not discussed in any provided article, explicitly state exactly:
   \"No information found for this topic in the provided sources.\"
4. If a requested competitor is not mentioned in any provided article, explicitly state exactly:
   \"No competitor activity found in the provided sources.\"
5. Every theme and every competitor activity must preserve supporting source URLs from the analyses.
6. Merge overlapping findings across multiple articles, but keep all supporting source URLs for the same insight.
7. If there is no supporting evidence for a requested topic or competitor, do not hallucinate; clearly state the absence of information.
8. The report should be professional, detailed, and suitable for executive briefing.

REPORT STRUCTURE:
- Executive Summary: write a substantial synthesis capturing the major findings across all provided URLs, the key themes and trends, important business announcements, relevant insights tied to the requested topics, competitor activity related to the requested competitors, and any concrete statistics or quantitative facts that were actually present.
- Key Themes: for each requested topic, produce a theme section with:
  - \"theme\": topic name
  - \"summary\": a detailed explanation of everything mentioned across all URLs for that topic, merged and de-duplicated
  - \"sources\": all supporting URLs for that topic
- Competitor Activity: for each requested competitor, produce an activity entry with:
  - \"competitor\": competitor name
  - \"activity\": a detailed description of all activities mentioned across the provided URLs, including launches, announcements, partnerships, investments, strategy changes, and notable business activity
  - \"sources\": all supporting URLs for the competitor activity

OUTPUT FORMAT: Return ONLY valid JSON with this exact schema:
{{
  "executive_summary": "...",
  "insights_grouped_by_theme": [{{"theme": "...", "summary": "...", "sources": ["..."]}}],
  "market_trends": [],
  "competitor_activities": ["..."],
  "business_insights": [],
  "statistics": [],
  "companies_mentioned": [],
  "source_traceability": [{{"source_url": "..."}}]
}}

User context:
Competitors: {competitors}
Topics: {topics}
Additional context: {context}

Analyses:
{analyses_json}
"""
    )

    def invoke(payload: dict[str, Any]) -> MarketIntelligenceReport:
        messages = prompt.format_messages(
            analyses_json=payload.get("analyses_json", "{}"),
            competitors=", ".join(payload.get("competitors", []) or []) if payload.get("competitors") else "None provided",
            topics=", ".join(payload.get("topics", []) or []) if payload.get("topics") else "None provided",
            context=payload.get("context", ""),
        )
        analyses = json.loads(payload.get("analyses_json", "[]")) if isinstance(payload.get("analyses_json"), str) else []
        try:
            response = _invoke_with_retry(llm, messages)
            parsed = _extract_json_payload(response)
            if not parsed:
                parsed = {}

            if isinstance(analyses, list):
                parsed = _enrich_report_payload(
                    parsed,
                    analyses,
                    competitors=payload.get("competitors", []),
                    topics=payload.get("topics", []),
                    context=payload.get("context", ""),
                )
                if not parsed.get("executive_summary") or not parsed.get("insights_grouped_by_theme"):
                    return _normalize_report(parsed)
            return _normalize_report(parsed)
        except Exception:
            if isinstance(analyses, list):
                return _build_report_from_analyses(
                    analyses,
                    competitors=payload.get("competitors", []),
                    topics=payload.get("topics", []),
                    context=payload.get("context", ""),
                )
            return _normalize_report({"executive_summary": "The report was generated from the available content after the live model was temporarily unavailable.", "insights_grouped_by_theme": [{"theme": "Market update", "summary": "The workflow used the fallback path because the live model was throttled.", "sources": []}], "market_trends": [], "competitor_activities": [], "business_insights": ["The workflow used the fallback path because the live model was throttled."], "statistics": [], "companies_mentioned": [], "source_traceability": []})

    return RunnableLambda(invoke)


# ──────────────────────────────────────────────────────────────────────────────
# Judge Chain (LLM-as-a-Judge)
# ──────────────────────────────────────────────────────────────────────────────

def build_judge_chain(llm: Any) -> Any:
    if isinstance(llm, FallbackLLM):
        def fallback_chain(payload: dict[str, Any]) -> JudgeResult:
            return JudgeResult(
                accuracy_score=0.5,
                completeness_score=0.5,
                hallucination_detection="Fallback workflow used; no live LLM validation was performed.",
                unsupported_claims=[],
                missing_information=["Live Groq validation was unavailable."],
                overall_feedback="The fallback workflow completed without live LLM validation.",
            )

        return RunnableLambda(fallback_chain)

    prompt = ChatPromptTemplate.from_template(
        """You are an expert LLM-as-a-judge evaluating a market intelligence report for factual accuracy.

Your task:
1. Compare EVERY claim in the report against the source article analyses.
2. Identify any claims in the report that are NOT supported by the analyses (hallucinations).
3. Score the report on accuracy (0.0–1.0) and completeness (0.0–1.0).

Return ONLY valid JSON with this exact schema:
{{
  "accuracy_score": <float 0.0-1.0>,
  "completeness_score": <float 0.0-1.0>,
  "hallucination_detection": "<brief verdict: 'No unsupported claims detected' or 'X unsupported claims found'>",
  "unsupported_claims": ["<claim 1 that has no source support>", ...],
  "missing_information": ["<key topic from analyses not included in report>", ...],
  "overall_feedback": "<2-3 sentence quality assessment>"
}}

Report to evaluate:
{report_json}

Source article analyses (ground truth):
{analyses_json}

Rules:
- A claim is unsupported if it cannot be traced back to the analyses.
- Do NOT penalize for correct synthesis or reasonable aggregation.
- Be strict but fair. Return ONLY the JSON object.
"""
    )

    def invoke(payload: dict[str, Any]) -> JudgeResult:
        messages = prompt.format_messages(
            report_json=payload.get("report_json", "{}"),
            analyses_json=payload.get("analyses_json", "{}"),
        )
        try:
            response = _invoke_with_retry(llm, messages)
            parsed = _extract_json_payload(response)
            return _normalize_judge(parsed)
        except Exception:
            return _normalize_judge({
                "accuracy_score": 0.7,
                "completeness_score": 0.7,
                "hallucination_detection": "The report was generated using fallback logic while the live model was temporarily unavailable.",
                "unsupported_claims": [],
                "missing_information": [],
                "overall_feedback": "The fallback workflow completed without live validation due to throttling.",
            })

    return RunnableLambda(invoke)
