"""Smoke tests for scripts.ingest_news CLI."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest
from packages.core.news.models import FetchNewsResult, NewsArticle
from packages.core.news.rss_source import RSSNewsSource
from scripts import ingest_news as cli
from scripts.migrate import applied_versions, apply_migration, discover_migrations


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    p = tmp_path / "news.duckdb"
    with duckdb.connect(str(p)) as conn:
        applied_versions(conn)
        for path in discover_migrations():
            apply_migration(conn, path)
    return p


class _StubSource(RSSNewsSource):
    def __init__(self, results: list[FetchNewsResult]) -> None:
        self._results = results

    def fetch(self, since: datetime | None = None) -> list[FetchNewsResult]:
        return self._results


def _ok_result() -> FetchNewsResult:
    return FetchNewsResult(
        source="detik",
        fetched_at=datetime(2026, 5, 18, tzinfo=UTC),
        status="ok",
        articles=[
            NewsArticle(
                id=0,
                url="https://detik.com/a",
                title="A",
                source="detik",
                published_at=datetime(2026, 5, 18, tzinfo=UTC),
                fetched_at=datetime(2026, 5, 18, tzinfo=UTC),
            )
        ],
    )


def test_summarize_buckets_results() -> None:
    summary = cli.summarize(
        [
            _ok_result(),
            FetchNewsResult(
                source="cnbc",
                fetched_at=datetime(2026, 5, 18, tzinfo=UTC),
                status="partial",
                articles=[],
                error_message="no articles parsed",
            ),
            FetchNewsResult(
                source="kontan",
                fetched_at=datetime(2026, 5, 18, tzinfo=UTC),
                status="failed",
                articles=[],
                error_message="boom",
            ),
        ]
    )
    assert summary["articles_seen"] == 1
    assert summary["by_status"]["ok"] == ["detik"]
    assert summary["by_status"]["partial"] == ["cnbc"]
    assert summary["by_status"]["failed"] == ["kontan"]
    assert "cnbc" in summary["errors"]


def test_exit_code_classification() -> None:
    assert cli.exit_code([_ok_result()]) == cli.EXIT_OK
    partial = FetchNewsResult(
        source="x", fetched_at=datetime.now(UTC), status="partial", articles=[]
    )
    assert cli.exit_code([_ok_result(), partial]) == cli.EXIT_PARTIAL
    failed = FetchNewsResult(source="y", fetched_at=datetime.now(UTC), status="failed", articles=[])
    assert cli.exit_code([_ok_result(), failed]) == cli.EXIT_FAILED


def test_load_feed_urls_filters_by_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    feeds = cli.load_feed_urls(selected=["detik"])
    assert "detik" in feeds
    assert "cnbc" not in feeds
