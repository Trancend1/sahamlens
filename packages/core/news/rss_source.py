"""RSS news adapter. Always returns list[FetchNewsResult] — never raises through public API.

One result per configured feed. Status follows FetchStatus literal:
  - "ok"     → ≥1 article parsed
  - "partial" → feed reachable but yielded zero articles after dedup/filter
  - "failed"  → HTTP / parser failure
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from packages.core.news.dedup import article_id, canonical_url
from packages.core.news.models import FetchNewsResult, NewsArticle

logger = logging.getLogger(__name__)

USER_AGENT = "SahamLens/1.0 (personal use)"
DEFAULT_MIN_INTERVAL_S = 600.0
DEFAULT_BACKOFF_S: tuple[float, ...] = (1.0, 2.0, 4.0, 8.0)
DEFAULT_HTTP_TIMEOUT_S = 15.0

# Host-prefix → source_quality mapping. Falls back to "unknown".
SOURCE_QUALITY: Mapping[str, str] = {
    "detik": "reputable_media",
    "cnbc": "reputable_media",
    "kontan": "reputable_media",
    "idx": "official",
    "bisnis": "reputable_media",
}

FetcherFn = Callable[[str], bytes]


@dataclass
class _FeedState:
    last_fetch_at: float = 0.0
    etag: str | None = None
    last_modified: str | None = None


def _is_rate_limit_error(exc: BaseException) -> bool:
    if isinstance(exc, HTTPError) and exc.code == 429:
        return True
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "too many requests" in msg


class RSSNewsSource:
    name = "rss"

    def __init__(
        self,
        feed_urls: Mapping[str, str],
        *,
        min_interval_s: float = DEFAULT_MIN_INTERVAL_S,
        backoff_s: tuple[float, ...] = DEFAULT_BACKOFF_S,
        http_timeout_s: float = DEFAULT_HTTP_TIMEOUT_S,
        fetcher: FetcherFn | None = None,
        parser: Callable[[bytes], Any] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if not feed_urls:
            raise ValueError("feed_urls must be non-empty")
        self._feed_urls = dict(feed_urls)
        self._min_interval_s = min_interval_s
        self._backoff_s = backoff_s
        self._http_timeout_s = http_timeout_s
        self._fetcher = fetcher or self._default_fetcher
        self._parser = parser or self._default_parser
        self._clock = clock or time.monotonic
        self._states: dict[str, _FeedState] = {label: _FeedState() for label in feed_urls}

    def fetch(self, since: datetime | None = None) -> list[FetchNewsResult]:
        results: list[FetchNewsResult] = []
        for label, url in self._feed_urls.items():
            fetched_at = datetime.now(UTC)
            try:
                payload = self._fetch_with_backoff(label, url)
            except Exception as exc:  # public adapter never raises
                logger.warning("rss fetch failed for %s: %s", label, exc)
                results.append(
                    FetchNewsResult(
                        source=label,
                        fetched_at=fetched_at,
                        status="failed",
                        articles=[],
                        error_message=str(exc),
                    )
                )
                continue

            articles = self._parse_articles(label, payload, fetched_at, since)
            status: str = "ok" if articles else "partial"
            results.append(
                FetchNewsResult(
                    source=label,
                    fetched_at=fetched_at,
                    status=status,  # type: ignore[arg-type]
                    articles=articles,
                    error_message=None if articles else "no articles parsed",
                )
            )
        return results

    def _fetch_with_backoff(self, label: str, url: str) -> bytes:
        state = self._states[label]
        now = self._clock()
        gap = now - state.last_fetch_at
        if state.last_fetch_at and gap < self._min_interval_s:
            time.sleep(self._min_interval_s - gap)

        attempts = (0.0, *self._backoff_s)
        last_exc: Exception | None = None
        for delay in attempts:
            if delay:
                time.sleep(delay)
            try:
                payload = self._fetcher(url)
            except Exception as exc:
                last_exc = exc
                if _is_rate_limit_error(exc):
                    continue
                raise
            else:
                state.last_fetch_at = self._clock()
                return payload
        assert last_exc is not None
        raise last_exc

    def _parse_articles(
        self,
        label: str,
        payload: bytes,
        fetched_at: datetime,
        since: datetime | None,
    ) -> list[NewsArticle]:
        parsed = self._parser(payload)
        entries = getattr(parsed, "entries", None) or []
        articles: list[NewsArticle] = []
        seen_ids: set[int] = set()
        for entry in entries:
            article = self._entry_to_article(label, entry, fetched_at)
            if article is None:
                continue
            if since is not None and article.published_at < since:
                continue
            if article.id in seen_ids:
                continue
            seen_ids.add(article.id)
            articles.append(article)
        return articles

    def _entry_to_article(self, label: str, entry: Any, fetched_at: datetime) -> NewsArticle | None:
        link = _get_attr(entry, "link")
        title = _get_attr(entry, "title")
        if not link or not title:
            return None
        try:
            url = canonical_url(link)
        except ValueError:
            return None
        published = _parse_entry_date(entry)
        if published is None:
            published = fetched_at
        raw_summary = _get_attr(entry, "summary") or _get_attr(entry, "description")
        try:
            return NewsArticle(
                id=article_id(url),
                url=url,
                title=str(title).strip(),
                source=label,
                published_at=published,
                fetched_at=fetched_at,
                raw_summary=str(raw_summary).strip() if raw_summary else None,
            )
        except ValueError as exc:
            logger.warning("rss entry skipped (%s): %s", label, exc)
            return None

    def _default_fetcher(self, url: str) -> bytes:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=self._http_timeout_s) as resp:
            return bytes(resp.read())

    @staticmethod
    def _default_parser(payload: bytes) -> Any:
        import feedparser

        return feedparser.parse(payload)


def _get_attr(entry: Any, key: str) -> Any:
    if isinstance(entry, Mapping):
        return entry.get(key)
    return getattr(entry, key, None)


def _parse_entry_date(entry: Any) -> datetime | None:
    for key in ("published", "updated", "pubDate"):
        raw = _get_attr(entry, key)
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(str(raw))
        except (TypeError, ValueError):
            continue
        if dt is None:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    return None
