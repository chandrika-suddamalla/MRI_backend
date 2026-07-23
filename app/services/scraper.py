from __future__ import annotations

import logging
import re
from typing import List

import trafilatura

logger = logging.getLogger("market_research_api")


class ArticleScraper:
    """Extract and clean article content from URLs."""

    def scrape_articles(self, urls: List[str]) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        for url in urls:
            try:
                downloaded = trafilatura.fetch_url(url)
                if not downloaded:
                    logger.warning("No content fetched for %s", url)
                    continue

                extracted = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=False,
                    include_formatting=False,
                    output_format="txt",
                )
                cleaned_text = self._clean_text(extracted or "")

                if not cleaned_text:
                    fallback_text = self._fallback_text(downloaded, url)
                    cleaned_text = self._clean_text(fallback_text)

                if cleaned_text:
                    results.append({"url": url, "article_text": cleaned_text})
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Failed to scrape %s: %s", url, exc)
        return results

    def _clean_text(self, text: str) -> str:
        cleaned = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped:
                cleaned.append(stripped)
        return "\n".join(cleaned)

    def _fallback_text(self, html: str, url: str) -> str:
        title_match = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
        title = self._clean_text(title_match.group(1)) if title_match else ""

        body_text = re.sub(r"<script.*?</script>", " ", html, flags=re.I | re.S)
        body_text = re.sub(r"<style.*?</style>", " ", body_text, flags=re.I | re.S)
        body_text = re.sub(r"<[^>]+>", " ", body_text)
        body_text = re.sub(r"\s+", " ", body_text)
        body_text = self._clean_text(body_text)

        if title and body_text:
            return f"Title: {title}\nSource: {url}\nContent: {body_text[:4000]}"
        if title:
            return f"Title: {title}\nSource: {url}"
        return f"Source: {url}\nContent: {body_text[:4000]}"
