"""Tests for critique_trade_plan orchestrator."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import duckdb
import pytest
from packages.core.ai.critique_plan import critique_trade_plan
from packages.core.ai.prompts import PromptTemplate
from packages.core.ai.router import CircuitBreaker, CostBudget, ModelRouter
from packages.core.journal.models import TradePlan
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
        id="journal_critique",
        version=1,
        task="journal_critique",
        system="sys",
        user_template=(
            "{plan_id}/{symbol}/{setup_type}/{thesis}/{entry_plan}"
            "/{stop_level}/{invalidation}/{target}"
            "/{position_size_rupiah}/{max_loss_rupiah}/{emotion}"
        ),
    )


def _plan() -> TradePlan:
    return TradePlan(
        id=1_000_001,
        symbol="BBCA.JK",
        setup_type="breakout",
        thesis="Harga menembus resistance 9500",
        entry_plan="Beli saat close 9500",
        stop_level=9200.0,
        invalidation="Close di bawah 9200",
        target="10200",
        position_size_rupiah=10_000_000,
        max_loss_rupiah=300_000,
        created_at=datetime(2026, 5, 21, tzinfo=UTC),
    )


def _budget() -> CostBudget:
    return CostBudget(
        daily_usd_cap=10.0,
        per_model_caps={"claude-sonnet-4-6": 10.0},
        per_call_usd={"claude-sonnet-4-6": 0.01},
    )


def _valid_raw(plan_id: int = 1_000_001) -> dict[str, Any]:
    return {
        "plan_id": plan_id,
        "checks": [
            {
                "category": "thesis",
                "status": "ok",
                "finding": "Thesis jelas dengan level spesifik.",
                "suggested_question": "Apa yang membuat resistance 9500 signifikan?",
            },
            {
                "category": "invalidation",
                "status": "ok",
                "finding": "Invalidasi memiliki level konkret.",
                "suggested_question": "Sudah mempertimbangkan gap down?",
            },
            {
                "category": "risk",
                "status": "weak",
                "finding": "Max loss tercatat, tapi belum ada perbandingan dengan target.",
                "suggested_question": "Berapa risk/reward ratio yang diharapkan?",
            },
            {
                "category": "catalyst",
                "status": "missing",
                "finding": "Tidak ada katalis konkret.",
                "suggested_question": "Apa event atau data yang mendukung setup ini?",
            },
            {
                "category": "emotion",
                "status": "ok",
                "finding": "Kondisi emosi tidak disebutkan.",
                "suggested_question": "Sudah melewati cooling-off 24 jam?",
            },
            {
                "category": "liquidity",
                "status": "ok",
                "finding": "BBCA termasuk saham blue chip dengan likuiditas tinggi.",
                "suggested_question": "Apakah spread bid-ask masuk dalam hitungan biaya?",
            },
        ],
        "overall_risk_flag": "amber",
        "caveats": ["Catalyst tidak tercantum, verifikasi sebelum eksekusi."],
        "not_financial_advice": True,
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


def test_valid_output_returns_critique(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _MockProvider([_valid_raw()])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    result = critique_trade_plan(
        _plan(),
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    assert result is not None
    assert result.plan_id == 1_000_001
    assert result.overall_risk_flag == "amber"
    assert len(result.checks) == 6
    assert result.not_financial_advice is True
    assert len(result.caveats) >= 1


def test_provider_returns_none_returns_none(conn: duckdb.DuckDBPyConnection) -> None:
    provider = _MockProvider([None])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    result = critique_trade_plan(
        _plan(),
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    assert result is None


def test_invalid_schema_returns_none(conn: duckdb.DuckDBPyConnection) -> None:
    broken: dict[str, Any] = {"plan_id": 1, "checks": "not_a_list"}
    provider = _MockProvider([broken])
    router = ModelRouter()
    breaker = CircuitBreaker(_budget())

    result = critique_trade_plan(
        _plan(),
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
    exhausted_budget = CostBudget(
        daily_usd_cap=0.0001,
        per_model_caps={"claude-sonnet-4-6": 0.0001},
        per_call_usd={"claude-sonnet-4-6": 10.0},
    )
    breaker = CircuitBreaker(exhausted_budget)

    result = critique_trade_plan(
        _plan(),
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

    critique_trade_plan(
        _plan(),
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
        template=_tpl(),
    )

    rows = conn.execute("SELECT COUNT(*) FROM ai_log").fetchone()
    assert rows is not None
    assert rows[0] == 1
