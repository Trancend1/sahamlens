"""Smoke tests for scripts.summarize_news CLI."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import duckdb
import pytest
from packages.core.news.models import NewsArticle
from packages.core.news.repo import upsert_news_articles
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


def test_dry_run_uses_load_news_lacking_summary(conn: duckdb.DuckDBPyConnection) -> None:
    """Dry-run path should iterate pending and never write summary fields."""
    from scripts.summarize_news import _run_dry

    art = NewsArticle(
        id=0,
        url="https://detik.com/x",
        title="t",
        source="detik",
        published_at=datetime(2026, 5, 18, tzinfo=UTC),
        fetched_at=datetime(2026, 5, 18, tzinfo=UTC),
    )
    upsert_news_articles(conn, [art])

    calls: list[NewsArticle] = []

    def summarizer(article: NewsArticle, watchlist: list[str]) -> None:
        calls.append(article)
        return None

    ok, failed = _run_dry(conn, summarizer, watchlist=[], limit=10)
    assert ok == 0
    assert failed == 1
    assert len(calls) == 1

    # confirm DB not updated with summary fields
    row = conn.execute("SELECT summarized_at FROM news WHERE id = ?", [art.id]).fetchone()
    assert row is not None
    assert row[0] is None
