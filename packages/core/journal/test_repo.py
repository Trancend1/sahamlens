"""DuckDB integration tests for journal repo. Uses in-memory DB with all migrations."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import duckdb
import pytest
from packages.core.journal.models import TradePlan
from packages.core.journal.repo import create_plan, list_plans, load_plan, update_status
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


def _plan(**kwargs: object) -> TradePlan:
    defaults: dict[str, object] = {
        "id": 1_000_000,
        "symbol": "BBCA.JK",
        "setup_type": "breakout",
        "thesis": "Harga menembus resistance 9500",
        "entry_plan": "Beli saat close di atas 9500",
        "stop_level": 9200.0,
        "invalidation": "Close di bawah 9200",
        "target": "10200",
        "position_size_rupiah": 10_000_000,
        "max_loss_rupiah": 300_000,
        "created_at": datetime(2026, 5, 21, 10, 0, 0, tzinfo=UTC),
    }
    defaults.update(kwargs)
    return TradePlan.model_validate(defaults)


def test_create_then_load_roundtrip(conn: duckdb.DuckDBPyConnection) -> None:
    plan = _plan()
    create_plan(conn, plan)
    loaded = load_plan(conn, plan.id)
    assert loaded is not None
    assert loaded.id == plan.id
    assert loaded.symbol == "BBCA.JK"
    assert loaded.setup_type == "breakout"
    assert loaded.thesis == plan.thesis
    assert loaded.stop_level == pytest.approx(9200.0)
    assert loaded.position_size_rupiah == 10_000_000
    assert loaded.max_loss_rupiah == 300_000
    assert loaded.status == "planned"


def test_load_nonexistent_returns_none(conn: duckdb.DuckDBPyConnection) -> None:
    assert load_plan(conn, 99999) is None


def test_list_all_plans(conn: duckdb.DuckDBPyConnection) -> None:
    create_plan(conn, _plan(id=1_000_001, symbol="BBCA.JK"))
    create_plan(conn, _plan(id=1_000_002, symbol="TLKM.JK"))
    plans = list_plans(conn)
    assert len(plans) == 2


def test_list_filter_by_symbol(conn: duckdb.DuckDBPyConnection) -> None:
    create_plan(conn, _plan(id=1_000_001, symbol="BBCA.JK"))
    create_plan(conn, _plan(id=1_000_002, symbol="TLKM.JK"))
    bbca_plans = list_plans(conn, symbol="BBCA")
    assert len(bbca_plans) == 1
    assert bbca_plans[0].symbol == "BBCA.JK"


def test_list_filter_by_status(conn: duckdb.DuckDBPyConnection) -> None:
    create_plan(conn, _plan(id=1_000_001, status="planned"))
    create_plan(conn, _plan(id=1_000_002, status="open"))
    planned = list_plans(conn, status="planned")
    assert len(planned) == 1
    assert planned[0].status == "planned"


def test_update_status_to_open(conn: duckdb.DuckDBPyConnection) -> None:
    plan = _plan()
    create_plan(conn, plan)
    update_status(conn, plan.id, "open")
    loaded = load_plan(conn, plan.id)
    assert loaded is not None
    assert loaded.status == "open"
    assert loaded.reviewed_at is None


def test_update_status_to_closed_sets_reviewed_at(conn: duckdb.DuckDBPyConnection) -> None:
    plan = _plan()
    create_plan(conn, plan)
    update_status(conn, plan.id, "closed", result_rupiah=500_000, lesson="Stop terlalu dekat")
    loaded = load_plan(conn, plan.id)
    assert loaded is not None
    assert loaded.status == "closed"
    assert loaded.result_rupiah == 500_000
    assert loaded.lesson == "Stop terlalu dekat"
    assert loaded.reviewed_at is not None


def test_update_status_to_skipped(conn: duckdb.DuckDBPyConnection) -> None:
    plan = _plan()
    create_plan(conn, plan)
    update_status(conn, plan.id, "skipped")
    loaded = load_plan(conn, plan.id)
    assert loaded is not None
    assert loaded.status == "skipped"
    assert loaded.reviewed_at is not None


def test_list_ordered_by_created_at_desc(conn: duckdb.DuckDBPyConnection) -> None:
    create_plan(conn, _plan(id=1_000_001, created_at=datetime(2026, 5, 20, tzinfo=UTC)))
    create_plan(conn, _plan(id=1_000_002, created_at=datetime(2026, 5, 21, tzinfo=UTC)))
    plans = list_plans(conn)
    assert plans[0].id == 1_000_002  # newer first
    assert plans[1].id == 1_000_001


def test_emotion_optional_roundtrip(conn: duckdb.DuckDBPyConnection) -> None:
    plan = _plan(emotion="fearful")
    create_plan(conn, plan)
    loaded = load_plan(conn, plan.id)
    assert loaded is not None
    assert loaded.emotion == "fearful"
