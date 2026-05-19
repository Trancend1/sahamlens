"""End-to-end pipeline with stub source + stub summarizer."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import duckdb
import pytest
from packages.core.news.models import FetchNewsResult, NewsArticle, NewsSummary
from packages.core.news.pipeline import ingest_news, summarize_pending
from packages.core.news.rss_source import RSSNewsSource
from scripts.migrate import applied_versions, apply_migration, discover_migrations


@pytest.fixture
def conn() -> Iterator[duckdb.DuckDBPyConnection]:
    c = duckdb.connect(":memory:")
    applied_versions(c)
    for path in discover_migrations():
        apply_migration(c, path)
    try:
        yield c
    finally:
        c.close()


class _StubSource(RSSNewsSource):
    def __init__(self, results: list[FetchNewsResult]) -> None:
        self._results = results

    def fetch(self, since: datetime | None = None) -> list[FetchNewsResult]:
        return self._results


def test_ingest_persists_ok_results(conn: duckdb.DuckDBPyConnection) -> None:
    art = NewsArticle(
        id=0,
        url="https://detik.com/a",
        title="A",
        source="detik",
        published_at=datetime(2026, 5, 18, tzinfo=UTC),
        fetched_at=datetime(2026, 5, 18, tzinfo=UTC),
    )
    src = _StubSource(
        [
            FetchNewsResult(
                source="detik",
                fetched_at=datetime(2026, 5, 18, tzinfo=UTC),
                status="ok",
                articles=[art],
            )
        ]
    )
    ingest_news(conn, src)
    row = conn.execute("SELECT COUNT(*) FROM news").fetchone()
    assert row is not None
    assert row[0] == 1


def test_summarize_pending_counts_success_and_failure(conn: duckdb.DuckDBPyConnection) -> None:
    arts = [
        NewsArticle(
            id=0,
            url=f"https://detik.com/{i}",
            title=f"t{i}",
            source="detik",
            published_at=datetime(2026, 5, 18, tzinfo=UTC),
            fetched_at=datetime(2026, 5, 18, tzinfo=UTC),
        )
        for i in range(3)
    ]
    src = _StubSource(
        [
            FetchNewsResult(
                source="detik",
                fetched_at=datetime(2026, 5, 18, tzinfo=UTC),
                status="ok",
                articles=arts,
            )
        ]
    )
    ingest_news(conn, src)

    def summarizer(article: NewsArticle, watchlist: list[str]) -> NewsSummary | None:
        if "1" in article.url:
            return None
        return NewsSummary(
            news_id=article.id,
            url=article.url,
            summary="ok.",
            affected_tickers=[],
            sentiment_label="neutral",
            caveats=[],
            source_quality="reputable_media",
            confidence=0.9,
            not_financial_advice=True,
            prompt_template_id="news_summary.v1",
            model="claude-haiku-4-5-20251001",
            summarized_at=datetime(2026, 5, 18, tzinfo=UTC),
        )

    ok, failed = summarize_pending(conn, summarizer, watchlist=[], limit=10)
    assert ok == 2
    assert failed == 1
