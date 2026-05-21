"""Tests for generate_stock_brief orchestrator."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import duckdb
import pytest
from packages.core.ai.generate_brief import generate_stock_brief
from packages.core.ai.models import StockBrief
from packages.core.ai.prompts import PromptTemplate
from packages.core.ai.router import CircuitBreaker, CostBudget, ModelRouter
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
        id="stock_brief",
        version=1,
        task="daily_brief",
        system="sys",
        user_template="{symbol}/{analysis_date}/{context_text}",
    )


def _budget() -> CostBudget:
    return CostBudget(
        daily_usd_cap=10.0,
        per_model_caps={"claude-sonnet-4-6": 10.0},
        per_call_usd={"claude-sonnet-4-6": 0.01},
    )


def _valid_raw() -> dict[str, Any]:
    return {
        "evidence": [
            {
                "type": "price",
                "value": "Close 9500",
                "source_ref": "price_history",
                "freshness": "2026-05-21",
            }
        ],
        "bullish_view": "MA 50 mendukung harga saat ini.",
        "bearish_view": "Volume menurun, sinyal lemah.",
        "uncertainty": "Data fundamental tidak tersedia di sistem.",
        "caveats": ["Analisis terbatas pada indikator teknikal."],
        "beginner_explanation": "Harga bergerak di atas MA 50, sinyal moderat.",
        "suggested_next_question": "Bagaimana posisi RSI dibanding minggu lalu?",
    }


class _MockProvider:
    def __init__(self, outputs: list[dict[str, Any] | None]) -> None:
        self._outputs = outputs
        self.calls = 0
        self.name = "mock"

    def complete_json(self, **_kwargs: Any) -> dict[str, Any] | None:
        idx = min(self.calls, len(self._outputs) - 1)
        self.calls += 1
        return self._outputs[idx]


def test_valid_output_returns_brief(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _MockProvider([_valid_raw()])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    result = generate_stock_brief(
        "BBCA",
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    assert result is not None
    assert isinstance(result, StockBrief)
    assert result.symbol == "BBCA.JK"
    assert result.not_financial_advice is True
    assert len(result.evidence) >= 1
    assert len(result.caveats) >= 1


def test_provider_returns_none(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _MockProvider([None])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    result = generate_stock_brief(
        "BBCA",
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    assert result is None


def test_invalid_schema_returns_none(conn: duckdb.DuckDBPyConnection) -> None:
    broken: dict[str, Any] = {"evidence": "not_a_list"}
    provider = _MockProvider([broken])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    result = generate_stock_brief(
        "BBCA",
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    assert result is None


def test_budget_exceeded_returns_none(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _MockProvider([_valid_raw()])
    router = ModelRouter()
    exhausted = CostBudget(
        daily_usd_cap=0.0001,
        per_model_caps={"claude-sonnet-4-6": 0.0001},
        per_call_usd={"claude-sonnet-4-6": 10.0},
    )
    breaker = CircuitBreaker(exhausted)

    result = generate_stock_brief(
        "BBCA",
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    assert result is None
    assert provider.calls == 0


def test_banned_phrase_retries_then_fails(conn: duckdb.DuckDBPyConnection) -> None:
    banned = dict(_valid_raw())
    banned["bullish_view"] = "Saham BBCA akan naik pekan depan."
    provider = _MockProvider([banned, banned, banned])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    result = generate_stock_brief(
        "BBCA",
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    assert result is None
    assert provider.calls == 3


def test_successful_call_logs_to_ai_log(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _MockProvider([_valid_raw()])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    generate_stock_brief(
        "BBCA",
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    rows = conn.execute("SELECT COUNT(*) FROM ai_log").fetchone()
    assert rows is not None
    assert rows[0] == 1
