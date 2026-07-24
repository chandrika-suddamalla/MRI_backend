"""Safe webpage download and main-text extraction utilities."""

from __future__ import annotations

import ipaddress
import logging
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger("market_research_api.scraper")


class SourceExtractionError(Exception):
    """Raised when a source cannot be fetched or does not contain article text."""


@dataclass(frozen=True)
class ExtractedSource:
    url: str
    text: str
    title: str | None = None


def _is_public_http_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False

    try:
        addresses = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        return False

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            return False
    return True


class TrafilaturaScraper:
    """Downloads public web pages and extracts their primary readable text."""

    def extract(self, url: str) -> ExtractedSource:
        # Import lazily so configuration/health endpoints remain available if a
        # deployment has not yet installed Trafilatura's native dependencies.
        try:
            import trafilatura
        except ImportError as exc:
            raise SourceExtractionError(
                "Trafilatura is unavailable. Install backend requirements before extracting sources."
            ) from exc

        if not _is_public_http_url(url):
            raise SourceExtractionError("Only publicly reachable http(s) URLs are allowed.")

        logger.info("Downloading source with Trafilatura: %s", url)
        try:
            downloaded = trafilatura.fetch_url(url)
        except Exception as exc:
            raise SourceExtractionError(f"Could not download this URL: {exc}") from exc

        if not downloaded:
            raise SourceExtractionError("Trafilatura could not download any content from this URL.")

        text = trafilatura.extract(
            downloaded,
            url=url,
            include_comments=False,
            include_tables=True,
            favor_precision=True,
        )
        if not text or len(text.strip()) < 80:
            raise SourceExtractionError("No readable article text was found on this URL.")

        metadata = trafilatura.extract_metadata(downloaded, default_url=url)
        logger.info(
            "Extracted %d characters from %s\n--- EXTRACTED CONTENT START ---\n%s\n--- EXTRACTED CONTENT END ---",
            len(text.strip()),
            url,
            text.strip(),
        )
        return ExtractedSource(
            url=url,
            text=text.strip(),
            title=metadata.title if metadata else None,
        )

    def scrape_articles(self, urls: list[str]) -> list[dict]:
        """Extract and clean all usable sources; callers can retain individual failures."""
        from app.services.text_cleaning import clean_article_text
        articles = []
        for url in urls:
            source = self.extract(url)
            articles.append({"url": source.url, "title": source.title, "article_text": clean_article_text(source.text)})
        return articles
