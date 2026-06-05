"""DuckDB persistence for manual-first earnings workflow."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

import duckdb
from packages.core.earnings.models import (
    EarningsEvent,
    EarningsEventInput,
    EarningsSummary,
)


def create_earnings_event(
    conn: duckdb.DuckDBPyConnection,
    event_input: EarningsEventInput,
    *,
    event_id: str | None = None,
) -> EarningsEvent:
    event = EarningsEvent(
        id=event_id or f"earnings-event-{uuid4().hex}",
        ticker=event_input.ticker,
        period=event_input.period,
        event_date=event_input.event_date,
        source_type=event_input.source_type,
        source_ref=event_input.source_ref,
        status="planned",
        created_at=event_input.now,
        updated_at=event_input.now,
        notes=event_input.notes,
    )
    conn.execute(
        """
        INSERT INTO earnings_events
            (id, ticker, period, event_date, source_type, source_ref, status,
             created_at, updated_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            event.id,
            event.ticker,
            event.period,
            event.event_date.isoformat(),
            event.source_type,
            event.source_ref,
            event.status,
            event.created_at.isoformat(),
            event.updated_at.isoformat(),
            event.notes,
        ],
    )
    return event


def list_earnings_events(
    conn: duckdb.DuckDBPyConnection,
    *,
    include_archived: bool = False,
) -> list[EarningsEvent]:
    where = "" if include_archived else "WHERE status != 'archived'"
    rows = conn.execute(
        f"""
        SELECT id, ticker, period, event_date, source_type, source_ref, status,
               created_at, updated_at, notes
        FROM earnings_events
        {where}
        ORDER BY event_date DESC, created_at DESC
        """
    ).fetchall()
    return [_row_to_event(row) for row in rows]


def get_earnings_event(
    conn: duckdb.DuckDBPyConnection,
    event_id: str,
) -> EarningsEvent | None:
    row = conn.execute(
        """
        SELECT id, ticker, period, event_date, source_type, source_ref, status,
               created_at, updated_at, notes
        FROM earnings_events
        WHERE id = ?
        """,
        [event_id],
    ).fetchone()
    return _row_to_event(row) if row else None


def update_earnings_event_notes(
    conn: duckdb.DuckDBPyConnection,
    event_id: str,
    *,
    notes: str,
    now: datetime,
) -> EarningsEvent | None:
    conn.execute(
        """
        UPDATE earnings_events
        SET notes = ?, updated_at = ?
        WHERE id = ? AND status != 'archived'
        """,
        [notes.strip() or None, now.isoformat(), event_id],
    )
    return get_earnings_event(conn, event_id)


def archive_earnings_event(
    conn: duckdb.DuckDBPyConnection,
    event_id: str,
    *,
    now: datetime,
) -> EarningsEvent | None:
    conn.execute(
        """
        UPDATE earnings_events
        SET status = 'archived', updated_at = ?
        WHERE id = ?
        """,
        [now.isoformat(), event_id],
    )
    return get_earnings_event(conn, event_id)


def upsert_earnings_summary(
    conn: duckdb.DuckDBPyConnection,
    summary: EarningsSummary,
) -> EarningsSummary:
    conn.execute(
        """
        UPDATE earnings_events
        SET status = 'summarized', updated_at = ?
        WHERE id = ? AND status != 'summarized'
        """,
        [summary.generated_at.isoformat(), summary.earnings_event_id],
    )
    conn.execute(
        """
        INSERT INTO earnings_summaries
            (id, earnings_event_id, generated_at, summary_text, caveats,
             input_snapshot_json, confidence_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (id) DO UPDATE SET
            generated_at = EXCLUDED.generated_at,
            summary_text = EXCLUDED.summary_text,
            caveats = EXCLUDED.caveats,
            input_snapshot_json = EXCLUDED.input_snapshot_json,
            confidence_status = EXCLUDED.confidence_status
        """,
        [
            summary.id,
            summary.earnings_event_id,
            summary.generated_at.isoformat(),
            summary.summary_text,
            json.dumps(summary.caveats),
            json.dumps(summary.input_snapshot, sort_keys=True),
            summary.confidence_status,
        ],
    )
    return summary


def list_earnings_summaries(conn: duckdb.DuckDBPyConnection) -> list[EarningsSummary]:
    rows = conn.execute(
        """
        SELECT id, earnings_event_id, generated_at, summary_text, caveats,
               input_snapshot_json, confidence_status
        FROM earnings_summaries
        ORDER BY generated_at DESC, id
        """
    ).fetchall()
    return [_row_to_summary(row) for row in rows]


def get_earnings_summary_for_event(
    conn: duckdb.DuckDBPyConnection,
    event_id: str,
) -> EarningsSummary | None:
    row = conn.execute(
        """
        SELECT id, earnings_event_id, generated_at, summary_text, caveats,
               input_snapshot_json, confidence_status
        FROM earnings_summaries
        WHERE earnings_event_id = ?
        ORDER BY generated_at DESC
        LIMIT 1
        """,
        [event_id],
    ).fetchone()
    return _row_to_summary(row) if row else None


def new_summary_id() -> str:
    return f"earnings-summary-{uuid4().hex}"


def _row_to_event(row: tuple[object, ...]) -> EarningsEvent:
    return EarningsEvent.model_validate(
        {
            "id": str(row[0]),
            "ticker": str(row[1]),
            "period": str(row[2]),
            "event_date": str(row[3]),
            "source_type": str(row[4]),
            "source_ref": _optional_str(row[5]),
            "status": str(row[6]),
            "created_at": datetime.fromisoformat(str(row[7])),
            "updated_at": datetime.fromisoformat(str(row[8])),
            "notes": _optional_str(row[9]),
        }
    )


def _row_to_summary(row: tuple[object, ...]) -> EarningsSummary:
    return EarningsSummary.model_validate(
        {
            "id": str(row[0]),
            "earnings_event_id": str(row[1]),
            "generated_at": datetime.fromisoformat(str(row[2])),
            "summary_text": str(row[3]),
            "caveats": json.loads(str(row[4])),
            "input_snapshot": json.loads(str(row[5])),
            "confidence_status": str(row[6]),
        }
    )


def _optional_str(value: object) -> str | None:
    return str(value) if value is not None else None
