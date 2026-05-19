"""ModelRouter + CircuitBreaker + budget loader."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest
from packages.core.ai.router import (
    BudgetExceeded,
    CircuitBreaker,
    CostBudget,
    ModelRouter,
    load_budget,
)
from packages.core.news.repo import log_ai_call
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


def test_model_router_default_news_summary() -> None:
    router = ModelRouter()
    assert router.select("news_summary").startswith("claude-haiku")


def test_model_router_overrides() -> None:
    router = ModelRouter(overrides={"news_summary": "custom-model"})
    assert router.select("news_summary") == "custom-model"


def test_circuit_breaker_passes_under_cap(conn: duckdb.DuckDBPyConnection) -> None:
    budget = CostBudget(
        daily_usd_cap=1.0,
        per_model_caps={"m": 1.0},
        per_call_usd={"m": 0.01},
    )
    breaker = CircuitBreaker(budget)
    breaker.check(conn, "m")  # zero calls today → no raise


def test_circuit_breaker_trips_when_projected_over_cap(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    budget = CostBudget(
        daily_usd_cap=0.05,
        per_model_caps={"m": 0.05},
        per_call_usd={"m": 0.04},
    )
    breaker = CircuitBreaker(budget)
    log_ai_call(
        conn,
        prompt_template_id="t",
        model="m",
        input_context="",
        output="",
        confidence=None,
        caveats_count=0,
    )
    with pytest.raises(BudgetExceeded):
        breaker.check(conn, "m")


def test_load_budget_falls_back_to_example(tmp_path: Path) -> None:
    # When no override path provided, loader falls back to example file in repo.
    budget = load_budget()
    assert budget.daily_usd_cap > 0
