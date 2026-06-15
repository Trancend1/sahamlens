"""Exposure boundary: aggregate-only, never leaks lots/avg_price/value."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
from packages.core.agent.exposure import exposure_summary
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.portfolio.models import PortfolioPosition
from packages.core.portfolio.repo import replace_positions
from scripts.migrate import applied_versions, apply_migration, discover_migrations


def _migrated_db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
    return conn


def _position(symbol: str, lots: int, avg_price: float) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        lots=lots,
        avg_price=avg_price,
        imported_at=datetime.now(UTC),
        source="csv",
    )


def test_empty_portfolio_returns_zeroed_summary(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        summary = exposure_summary(conn)
    assert summary.position_count == 0
    assert summary.holdings == []
    assert summary.top_concentration_pct == 0.0
    assert summary.top3_concentration_pct == 0.0


def test_weights_are_relative_value_concentration(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        replace_positions(
            conn,
            [
                _position("BBCA", lots=10, avg_price=9000.0),  # value 90_000 -> 75%
                _position("BBRI", lots=10, avg_price=3000.0),  # value 30_000 -> 25%
            ],
        )
        summary = exposure_summary(conn)

    weights = {h.symbol: h.weight_pct for h in summary.holdings}
    assert weights[normalize_ticker("BBCA")] == 75.0
    assert weights[normalize_ticker("BBRI")] == 25.0
    assert summary.top_concentration_pct == 75.0
    assert summary.top3_concentration_pct == 100.0


def test_summary_never_leaks_lots_avg_price_or_value(tmp_path: Path) -> None:
    # Distinctive sentinels: lots, avg_price, and their product must never appear.
    lots, avg_price = 7777, 9999.99
    leaked_value = str(int(lots * avg_price))  # 77769922
    with _migrated_db(tmp_path) as conn:
        replace_positions(conn, [_position("BBCA", lots=lots, avg_price=avg_price)])
        summary = exposure_summary(conn)

    payload = json.dumps(summary.model_dump(), ensure_ascii=False)
    assert str(lots) not in payload
    assert "9999.99" not in payload
    assert leaked_value not in payload
    # The only number a single holding exposes is its 100% relative weight.
    assert summary.holdings[0].weight_pct == 100.0


def test_zero_value_portfolio_is_safe(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        replace_positions(conn, [_position("BBCA", lots=0, avg_price=0.0)])
        summary = exposure_summary(conn)
    assert summary.position_count == 1
    assert summary.holdings[0].weight_pct == 0.0
    assert summary.top_concentration_pct == 0.0
