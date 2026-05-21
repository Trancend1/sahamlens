"""DuckDB persistence for trade journal plans.

ID generation: int(time.time() * 1_000_000) — microsecond epoch, collision-free single-user.
Connection is caller-managed (same pattern as packages/core/indicators/repo.py).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import duckdb
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.journal.models import TradePlan, TradeStatus


def _new_id() -> int:
    return int(time.time() * 1_000_000)


def create_plan(conn: duckdb.DuckDBPyConnection, plan: TradePlan) -> None:
    """Insert a new trade plan. Raises IntegrityError if id already exists."""
    conn.execute(
        """
        INSERT INTO journal (
            id, symbol, setup_type, thesis, entry_plan, stop_level,
            invalidation, target, position_size_rupiah, max_loss_rupiah,
            emotion, status, result_rupiah, lesson, created_at, reviewed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            plan.id,
            plan.symbol,
            plan.setup_type,
            plan.thesis,
            plan.entry_plan,
            plan.stop_level,
            plan.invalidation,
            plan.target,
            plan.position_size_rupiah,
            plan.max_loss_rupiah,
            plan.emotion,
            plan.status,
            plan.result_rupiah,
            plan.lesson,
            plan.created_at.isoformat(),
            plan.reviewed_at.isoformat() if plan.reviewed_at else None,
        ],
    )


def load_plan(conn: duckdb.DuckDBPyConnection, plan_id: int) -> TradePlan | None:
    """Return TradePlan by id, or None if not found."""
    row = conn.execute(
        """
        SELECT id, symbol, setup_type, thesis, entry_plan, stop_level,
               invalidation, target, position_size_rupiah, max_loss_rupiah,
               emotion, status, result_rupiah, lesson, created_at, reviewed_at
        FROM journal WHERE id = ?
        """,
        [plan_id],
    ).fetchone()
    if row is None:
        return None
    return _row_to_plan(row)


def list_plans(
    conn: duckdb.DuckDBPyConnection,
    symbol: str | None = None,
    status: TradeStatus | None = None,
) -> list[TradePlan]:
    """Return plans ordered by created_at DESC. Optionally filter by symbol and/or status."""
    filters: list[str] = []
    params: list[object] = []
    if symbol is not None:
        filters.append("symbol = ?")
        params.append(normalize_ticker(symbol))
    if status is not None:
        filters.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = conn.execute(
        f"""
        SELECT id, symbol, setup_type, thesis, entry_plan, stop_level,
               invalidation, target, position_size_rupiah, max_loss_rupiah,
               emotion, status, result_rupiah, lesson, created_at, reviewed_at
        FROM journal {where}
        ORDER BY created_at DESC
        """,
        params,
    ).fetchall()
    return [_row_to_plan(r) for r in rows]


def update_status(
    conn: duckdb.DuckDBPyConnection,
    plan_id: int,
    status: TradeStatus,
    *,
    result_rupiah: int | None = None,
    lesson: str | None = None,
) -> None:
    """Transition a plan to a new status. Optionally record result and lesson."""
    reviewed_at = datetime.now(UTC).isoformat() if status in ("closed", "skipped") else None
    conn.execute(
        """
        UPDATE journal
        SET status = ?,
            result_rupiah = COALESCE(?, result_rupiah),
            lesson = COALESCE(?, lesson),
            reviewed_at = COALESCE(?, reviewed_at)
        WHERE id = ?
        """,
        [status, result_rupiah, lesson, reviewed_at, plan_id],
    )


def _row_to_plan(row: tuple[Any, ...]) -> TradePlan:
    return TradePlan(
        id=int(row[0]),
        symbol=str(row[1]),
        setup_type=row[2],
        thesis=str(row[3]),
        entry_plan=str(row[4]),
        stop_level=float(row[5]),
        invalidation=str(row[6]),
        target=str(row[7]),
        position_size_rupiah=int(row[8]),
        max_loss_rupiah=int(row[9]),
        emotion=row[10],
        status=row[11],
        result_rupiah=int(row[12]) if row[12] is not None else None,
        lesson=str(row[13]) if row[13] is not None else None,
        created_at=datetime.fromisoformat(str(row[14])),
        reviewed_at=datetime.fromisoformat(str(row[15])) if row[15] is not None else None,
    )
