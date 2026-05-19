"""summarize_news orchestrator: ticker intersection, retries, confidence adjust."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import duckdb
import pytest
from packages.core.ai.prompts import PromptTemplate
from packages.core.ai.router import (
    CircuitBreaker,
    CostBudget,
    ModelRouter,
)
from packages.core.ai.summarize_news import (
    adjust_confidence,
    detect_affected_tickers,
    summarize_news,
)
from packages.core.news.models import NewsArticle
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


def _tpl() -> PromptTemplate:
    return PromptTemplate(
        id="news_summary",
        version=1,
        task="news_summary",
        system="sys",
        user_template="{title}/{source}/{published_at}/{url}/{raw_summary}/{watchlist_tickers}/{news_id}",
    )


def _article() -> NewsArticle:
    return NewsArticle(
        id=42,
        url="https://detik.com/news/bbca",
        title="BBCA naikkan target kredit",
        source="detik",
        published_at=datetime(2026, 5, 17, tzinfo=UTC),
        fetched_at=datetime(2026, 5, 18, tzinfo=UTC),
        raw_summary="BBCA dan TLKM rilis laporan.",
    )


def _budget() -> CostBudget:
    return CostBudget(
        daily_usd_cap=10.0,
        per_model_caps={"claude-haiku-4-5-20251001": 10.0},
        per_call_usd={"claude-haiku-4-5-20251001": 0.001},
    )


class _Provider:
    def __init__(self, outputs: list[dict[str, Any] | None]) -> None:
        self._outputs = outputs
        self.calls: int = 0
        self.name = "fake"

    def complete_json(self, **_kwargs: Any) -> dict[str, Any] | None:
        idx = min(self.calls, len(self._outputs) - 1)
        self.calls += 1
        return self._outputs[idx]


def test_detect_affected_tickers_matches_bare_and_dot_jk() -> None:
    text = "Hari ini BBCA dan TLKM.JK menguat."
    assert set(detect_affected_tickers(text, ["BBCA.JK", "TLKM.JK", "ASII.JK"])) == {
        "BBCA.JK",
        "TLKM.JK",
    }


def test_adjust_confidence_downweights_when_no_tickers() -> None:
    assert adjust_confidence(0.8, has_tickers=False, age_days=0) == pytest.approx(0.7)


def test_adjust_confidence_downweights_when_stale() -> None:
    assert adjust_confidence(0.8, has_tickers=True, age_days=10) == pytest.approx(0.75)


def test_summarize_returns_none_when_provider_returns_none(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _Provider([None])
    result = summarize_news(
        _article(),
        watchlist=["BBCA"],
        provider=provider,
        router=ModelRouter(),
        breaker=CircuitBreaker(_budget()),
        conn=conn,
        template=_tpl(),
    )
    assert result is None
    log = conn.execute("SELECT COUNT(*) FROM ai_log").fetchone()
    assert log is not None
    assert log[0] == 1


def test_summarize_intersects_llm_tickers_with_watchlist(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _Provider(
        [
            {
                "summary": "BBCA naikkan target.",
                "affected_tickers": ["BBCA.JK", "GOTO.JK"],  # GOTO not in watchlist
                "sentiment_label": "bullish",
                "caveats": [],
                "confidence": 0.9,
            }
        ]
    )
    result = summarize_news(
        _article(),
        watchlist=["BBCA", "TLKM"],
        provider=provider,
        router=ModelRouter(),
        breaker=CircuitBreaker(_budget()),
        conn=conn,
        template=_tpl(),
        now=datetime(2026, 5, 18, tzinfo=UTC),
    )
    assert result is not None
    assert result.affected_tickers == ["BBCA.JK"]


def test_summarize_retries_on_banned_phrase(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _Provider(
        [
            {
                "summary": "Strong buy now BBCA.",
                "affected_tickers": ["BBCA.JK"],
                "sentiment_label": "bullish",
                "caveats": [],
                "confidence": 0.9,
            },
            {
                "summary": "BBCA naikkan target kredit.",
                "affected_tickers": ["BBCA.JK"],
                "sentiment_label": "bullish",
                "caveats": [],
                "confidence": 0.9,
            },
        ]
    )
    result = summarize_news(
        _article(),
        watchlist=["BBCA"],
        provider=provider,
        router=ModelRouter(),
        breaker=CircuitBreaker(_budget()),
        conn=conn,
        template=_tpl(),
        now=datetime(2026, 5, 18, tzinfo=UTC),
    )
    assert result is not None
    assert provider.calls == 2


def test_summarize_returns_none_after_three_banned_retries(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    bad = {
        "summary": "Strong buy now BBCA.",
        "affected_tickers": ["BBCA.JK"],
        "sentiment_label": "bullish",
        "caveats": [],
        "confidence": 0.9,
    }
    provider = _Provider([bad, bad, bad])
    result = summarize_news(
        _article(),
        watchlist=["BBCA"],
        provider=provider,
        router=ModelRouter(),
        breaker=CircuitBreaker(_budget()),
        conn=conn,
        template=_tpl(),
    )
    assert result is None
    assert provider.calls == 3


def test_summarize_skips_when_budget_exceeded(conn: duckdb.DuckDBPyConnection) -> None:
    tight_budget = CostBudget(
        daily_usd_cap=0.0001,
        per_model_caps={"claude-haiku-4-5-20251001": 0.0001},
        per_call_usd={"claude-haiku-4-5-20251001": 0.01},
    )
    provider = _Provider([{"summary": "x.", "sentiment_label": "neutral", "confidence": 0.9}])
    result = summarize_news(
        _article(),
        watchlist=["BBCA"],
        provider=provider,
        router=ModelRouter(),
        breaker=CircuitBreaker(tight_budget),
        conn=conn,
        template=_tpl(),
    )
    assert result is None
    assert provider.calls == 0
