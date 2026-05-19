"""High-level orchestration: fetch → dedup → persist; then summarize backlog.

Splits ingest and summarize so cost-cap / parallelism can be controlled per step.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

import duckdb
from packages.core.news.models import FetchNewsResult, NewsArticle, NewsSummary
from packages.core.news.repo import (
    load_news_lacking_summary,
    upsert_news_articles,
    upsert_news_summary,
)
from packages.core.news.rss_source import RSSNewsSource

SummarizerFn = Callable[[NewsArticle, list[str]], NewsSummary | None]


def ingest_news(
    conn: duckdb.DuckDBPyConnection,
    source: RSSNewsSource,
    *,
    since: datetime | None = None,
) -> list[FetchNewsResult]:
    """Fetch all configured feeds, dedup by canonical url, persist raw articles."""
    results = source.fetch(since=since)
    for result in results:
        if result.articles:
            upsert_news_articles(conn, result.articles)
    return results


def summarize_pending(
    conn: duckdb.DuckDBPyConnection,
    summarizer: SummarizerFn,
    *,
    watchlist: list[str],
    limit: int = 20,
) -> tuple[int, int]:
    """Iterate articles lacking summary; call summarizer; persist results.

    Returns (succeeded, failed) counts. Summarizer returning None counts as failed.
    """
    pending = load_news_lacking_summary(conn, limit=limit)
    succeeded = 0
    failed = 0
    for article in pending:
        summary = summarizer(article, watchlist)
        if summary is None:
            failed += 1
            continue
        upsert_news_summary(conn, summary)
        succeeded += 1
    return succeeded, failed
