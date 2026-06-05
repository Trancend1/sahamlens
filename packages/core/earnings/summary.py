"""Manual-first earnings summary generation."""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb
from packages.core.earnings.models import EarningsSummary, validate_summary_notes
from packages.core.earnings.repo import (
    get_earnings_event,
    new_summary_id,
    upsert_earnings_summary,
)


def generate_earnings_summary(
    conn: duckdb.DuckDBPyConnection,
    event_id: str,
    *,
    generated_at: datetime | None = None,
) -> EarningsSummary:
    event = get_earnings_event(conn, event_id)
    if event is None:
        raise ValueError("not_found: earnings event was not found")

    notes = validate_summary_notes(event.notes)
    now = generated_at or datetime.now(UTC)
    snapshot = {
        "ticker": event.ticker,
        "period": event.period,
        "event_date": event.event_date.isoformat(),
        "source_type": event.source_type,
        "source_ref": event.source_ref,
        "status_before_summary": event.status,
        "notes_excerpt": _excerpt(notes),
        "created_at": event.created_at.isoformat(),
        "updated_at": event.updated_at.isoformat(),
    }
    summary = EarningsSummary(
        id=new_summary_id(),
        earnings_event_id=event.id,
        generated_at=now,
        summary_text=(
            f"Post-event review for {event.ticker} {event.period} based on manual notes "
            f"and available local data. Key context: {_excerpt(notes, limit=240)}"
        ),
        caveats=[
            "Based on manual notes and available local data; not an instruction.",
            "No automated scraping or external refresh was performed for this summary.",
            "Review source context and data confidence before using this in a decision workflow.",
        ],
        input_snapshot=snapshot,
        confidence_status="manual_only",
    )
    return upsert_earnings_summary(conn, summary)


def _excerpt(value: str, *, limit: int = 160) -> str:
    compact = " ".join(value.split())
    return compact if len(compact) <= limit else f"{compact[: limit - 3]}..."
