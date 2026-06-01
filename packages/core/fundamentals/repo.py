"""DuckDB persistence for lightweight fundamental snapshots."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

import duckdb
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.fundamentals.models import FundamentalSnapshot


def upsert_fundamental_snapshot(
    conn: duckdb.DuckDBPyConnection,
    snapshot: FundamentalSnapshot,
) -> int:
    conn.execute(
        """
        INSERT INTO fundamental_snapshots
            (symbol, period, statement_date, source, source_type, fetched_at, imported_at,
             data_fields, available_fields, missing_fields, completeness_state,
             confidence_level, confidence_score, caveat, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (symbol, period, source, fetched_at) DO UPDATE SET
            statement_date = EXCLUDED.statement_date,
            source_type = EXCLUDED.source_type,
            imported_at = EXCLUDED.imported_at,
            data_fields = EXCLUDED.data_fields,
            available_fields = EXCLUDED.available_fields,
            missing_fields = EXCLUDED.missing_fields,
            completeness_state = EXCLUDED.completeness_state,
            confidence_level = EXCLUDED.confidence_level,
            confidence_score = EXCLUDED.confidence_score,
            caveat = EXCLUDED.caveat,
            reason = EXCLUDED.reason
        """,
        [
            snapshot.symbol,
            snapshot.period,
            snapshot.statement_date.isoformat() if snapshot.statement_date else None,
            snapshot.source,
            snapshot.source_type,
            snapshot.fetched_at.isoformat(),
            snapshot.imported_at.isoformat(),
            json.dumps(snapshot.data_fields, sort_keys=True),
            json.dumps(snapshot.available_fields),
            json.dumps(snapshot.missing_fields),
            snapshot.completeness_state,
            snapshot.confidence_level,
            snapshot.confidence_score,
            snapshot.caveat,
            snapshot.reason,
        ],
    )
    return 1


def get_latest_fundamental_snapshot(
    conn: duckdb.DuckDBPyConnection,
    symbol: str,
) -> FundamentalSnapshot | None:
    rows = list_fundamental_snapshots(conn, symbol=symbol, limit=1)
    return rows[0] if rows else None


def list_fundamental_snapshots(
    conn: duckdb.DuckDBPyConnection,
    *,
    symbol: str | None = None,
    limit: int | None = None,
) -> list[FundamentalSnapshot]:
    where = ""
    params: list[object] = []
    if symbol is not None:
        where = "WHERE symbol = ?"
        params.append(normalize_ticker(symbol))
    limit_sql = ""
    if limit is not None:
        limit_sql = "LIMIT ?"
        params.append(limit)
    rows = conn.execute(
        f"""
        SELECT symbol, period, statement_date, source, source_type, fetched_at, imported_at,
               data_fields, available_fields, missing_fields, completeness_state,
               confidence_level, confidence_score, caveat, reason
        FROM fundamental_snapshots
        {where}
        ORDER BY fetched_at DESC, imported_at DESC, symbol
        {limit_sql}
        """,
        params,
    ).fetchall()
    return [_row_to_snapshot(row) for row in rows]


def _row_to_snapshot(row: tuple[object, ...]) -> FundamentalSnapshot:
    return FundamentalSnapshot.model_validate(
        {
            "symbol": str(row[0]),
            "period": str(row[1]),
            "statement_date": _optional_date(row[2]),
            "source": str(row[3]),
            "source_type": str(row[4]),
            "fetched_at": datetime.fromisoformat(str(row[5])),
            "imported_at": datetime.fromisoformat(str(row[6])),
            "data_fields": _json_dict(row[7]),
            "available_fields": _json_list(row[8]),
            "missing_fields": _json_list(row[9]),
            "completeness_state": str(row[10]),
            "confidence_level": str(row[11]),
            "confidence_score": float(str(row[12])),
            "caveat": _optional_str(row[13]),
            "reason": _optional_str(row[14]),
        }
    )


def _json_dict(value: object) -> dict[str, Any]:
    parsed = json.loads(str(value))
    if not isinstance(parsed, dict):
        raise ValueError("expected JSON object")
    return parsed


def _json_list(value: object) -> list[str]:
    parsed = json.loads(str(value))
    if not isinstance(parsed, list):
        raise ValueError("expected JSON list")
    return [str(item) for item in parsed]


def _optional_date(value: object) -> date | None:
    return date.fromisoformat(str(value)) if value is not None else None


def _optional_str(value: object) -> str | None:
    return str(value) if value is not None else None
