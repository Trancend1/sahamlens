"""Repo + DuckDB persistence: upsert, ticker filter, ai_log."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import duckdb
import pytest
from packages.core.news.models import NewsArticle, NewsSummary
from packages.core.news.repo import (
    daily_ai_spend,
    load_news_lacking_summary,
    load_recent_news_for_ticker,
    log_ai_call,
    upsert_news_articles,
    upsert_news_summary,
)
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


def _article(url: str, *, source: str = "detik", title: str = "judul") -> NewsArticle:
    return NewsArticle(
        id=0,
        url=url,
        title=title,
        source=source,
        published_at=datetime(2026, 5, 18, tzinfo=UTC),
        fetched_at=datetime(2026, 5, 18, 10, tzinfo=UTC),
    )


def _summary(news_id: int, *, tickers: list[str]) -> NewsSummary:
    return NewsSummary(
        news_id=news_id,
        url="https://x.com/a",
        summary="ringkasan satu.",
        affected_tickers=tickers,
        sentiment_label="neutral",
        caveats=["belum verifikasi"],
        source_quality="reputable_media",
        confidence=0.8,
        not_financial_advice=True,
        prompt_template_id="news_summary.v1",
        model="claude-haiku-4-5-20251001",
        summarized_at=datetime(2026, 5, 18, 11, tzinfo=UTC),
    )


def test_upsert_news_articles_idempotent(conn: duckdb.DuckDBPyConnection) -> None:
    art = _article("https://detik.com/a")
    upsert_news_articles(conn, [art])
    upsert_news_articles(conn, [art])
    count = conn.execute("SELECT COUNT(*) FROM news").fetchone()
    assert count is not None
    assert count[0] == 1


def test_upsert_sets_source_quality_for_known_source(conn: duckdb.DuckDBPyConnection) -> None:
    upsert_news_articles(conn, [_article("https://detik.com/a", source="detik")])
    row = conn.execute("SELECT source_quality FROM news").fetchone()
    assert row is not None
    assert row[0] == "reputable_media"


def test_upsert_source_quality_unknown_for_unmapped(conn: duckdb.DuckDBPyConnection) -> None:
    upsert_news_articles(conn, [_article("https://blog.test/x", source="randomblog")])
    row = conn.execute("SELECT source_quality FROM news").fetchone()
    assert row is not None
    assert row[0] == "unknown"


def test_upsert_summary_then_load_recent_for_ticker(conn: duckdb.DuckDBPyConnection) -> None:
    art = _article("https://detik.com/bbca-news")
    upsert_news_articles(conn, [art])
    summary = _summary(art.id, tickers=["BBCA.JK"])
    upsert_news_summary(conn, summary)

    recent = load_recent_news_for_ticker(conn, "BBCA", limit=5)
    assert len(recent) == 1
    assert recent[0].affected_tickers == ["BBCA.JK"]
    assert recent[0].summary == "ringkasan satu."


def test_load_recent_filters_other_tickers(conn: duckdb.DuckDBPyConnection) -> None:
    art = _article("https://detik.com/tlkm-news")
    upsert_news_articles(conn, [art])
    upsert_news_summary(conn, _summary(art.id, tickers=["TLKM.JK"]))

    recent = load_recent_news_for_ticker(conn, "BBCA", limit=5)
    assert recent == []


def test_load_pending_excludes_summarized(conn: duckdb.DuckDBPyConnection) -> None:
    a1 = _article("https://detik.com/x")
    a2 = _article("https://detik.com/y")
    upsert_news_articles(conn, [a1, a2])
    upsert_news_summary(conn, _summary(a1.id, tickers=[]))

    pending = load_news_lacking_summary(conn, limit=10)
    assert len(pending) == 1
    assert pending[0].id == a2.id


def test_log_ai_call_writes_row_and_returns_id(conn: duckdb.DuckDBPyConnection) -> None:
    log_id = log_ai_call(
        conn,
        prompt_template_id="news_summary.v1",
        model="claude-haiku-4-5-20251001",
        input_context='{"x":1}',
        output='{"y":2}',
        confidence=0.85,
        caveats_count=1,
    )
    row = conn.execute("SELECT id, model FROM ai_log WHERE id = ?", [log_id]).fetchone()
    assert row is not None
    assert row[0] == log_id
    assert row[1] == "claude-haiku-4-5-20251001"


def test_daily_spend_counts_by_day_prefix(conn: duckdb.DuckDBPyConnection) -> None:
    log_ai_call(
        conn,
        prompt_template_id="t",
        model="m",
        input_context="",
        output="",
        confidence=None,
        caveats_count=0,
    )
    today = datetime.now(UTC).date().isoformat()
    assert daily_ai_spend(conn, day_iso=today) >= 1
