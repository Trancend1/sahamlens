"""Tests for answer_stock_question orchestrator."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import duckdb
import pytest
from packages.core.ai.models import ChatResponse
from packages.core.ai.prompts import PromptTemplate
from packages.core.ai.router import CircuitBreaker, CostBudget, ModelRouter
from packages.core.ai.stock_chat import answer_stock_question
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
        id="stock_chat",
        version=1,
        task="stock_chat",
        system="sys",
        user_template="{symbol}/{context_text}/{prior_turns}/{question}",
    )


def _budget() -> CostBudget:
    return CostBudget(
        daily_usd_cap=10.0,
        per_model_caps={"claude-sonnet-4-6": 10.0},
        per_call_usd={"claude-sonnet-4-6": 0.01},
    )


def _valid_raw() -> dict[str, Any]:
    return {
        "answer": "RSI BBCA saat ini di 55, belum memasuki zona overbought.",
        "evidence": [
            {
                "type": "indicator",
                "value": "rsi_14=55.0",
                "source_ref": "indicator_cache",
                "freshness": "2026-05-21",
            }
        ],
        "caveats": ["RSI adalah indikator lagging, bukan prediksi arah."],
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


def test_valid_output_returns_response(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _MockProvider([_valid_raw()])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    result = answer_stock_question(
        "Bagaimana RSI BBCA?",
        "BBCA",
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    assert result is not None
    assert isinstance(result, ChatResponse)
    assert result.question == "Bagaimana RSI BBCA?"
    assert result.not_financial_advice is True
    assert len(result.caveats) >= 1


def test_provider_returns_none(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _MockProvider([None])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    result = answer_stock_question(
        "Bagaimana RSI?",
        "BBCA",
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    assert result is None


def test_invalid_schema_returns_none(conn: duckdb.DuckDBPyConnection) -> None:
    broken: dict[str, Any] = {"answer": "ok", "evidence": "bad", "caveats": []}
    provider = _MockProvider([broken])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    result = answer_stock_question(
        "Test",
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

    result = answer_stock_question(
        "Test",
        "BBCA",
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    assert result is None
    assert provider.calls == 0


def test_successful_call_logs_to_ai_log(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _MockProvider([_valid_raw()])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    answer_stock_question(
        "Bagaimana RSI?",
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
