from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, cast

import duckdb
import pytest
from packages.core.earnings import (
    EarningsEventInput,
    create_earnings_event,
    generate_earnings_summary,
    get_earnings_event,
    get_earnings_summary_for_event,
    list_earnings_events,
    list_earnings_summaries,
    update_earnings_event_notes,
)
from scripts.migrate import applied_versions, apply_migration, discover_migrations

NOW = datetime(2026, 6, 5, 10, 0, tzinfo=UTC)


def test_create_list_and_read_manual_earnings_event(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        event = create_earnings_event(
            conn,
            EarningsEventInput(
                ticker="BBCA",
                period="2026-Q2",
                event_date=date(2026, 7, 31),
                source_type="manual",
                source_ref="owner note",
                notes="Revenue grew compared with prior quarter; margin pressure needs review.",
                now=NOW,
            ),
        )

        assert event.id
        assert event.ticker == "BBCA.JK"
        assert event.status == "planned"
        assert list_earnings_events(conn) == [event]
        assert get_earnings_event(conn, event.id) == event


def test_event_validation_rejects_missing_and_invalid_values() -> None:
    with pytest.raises(ValueError, match="ticker"):
        EarningsEventInput(
            ticker="",
            period="2026-Q2",
            event_date=date(2026, 7, 31),
            source_type="manual",
            notes="Valid manual note.",
            now=NOW,
        )
    with pytest.raises(ValueError, match="source_type"):
        EarningsEventInput(
            ticker="BBCA",
            period="2026-Q2",
            event_date=date(2026, 7, 31),
            source_type=cast(Any, "scraped_feed"),
            notes="Valid manual note.",
            now=NOW,
        )


def test_generate_summary_from_manual_notes_with_caveats_and_snapshot(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        event = create_earnings_event(
            conn,
            EarningsEventInput(
                ticker="BBCA",
                period="2026-Q2",
                event_date=date(2026, 7, 31),
                source_type="manual",
                source_ref="owner note",
                notes="Revenue grew compared with prior quarter. Net margin softened. Management highlighted loan growth and funding cost pressure.",
                now=NOW,
            ),
        )

        summary = generate_earnings_summary(conn, event.id, generated_at=NOW)

        assert summary.earnings_event_id == event.id
        assert summary.confidence_status == "manual_only"
        assert "post-event review" in summary.summary_text.lower()
        assert "manual" in summary.summary_text.lower()
        assert summary.caveats
        assert "not an instruction" in " ".join(summary.caveats)
        assert summary.input_snapshot["ticker"] == "BBCA.JK"
        assert get_earnings_summary_for_event(conn, event.id) == summary
        assert list_earnings_summaries(conn) == [summary]
        refreshed = get_earnings_event(conn, event.id)
        assert refreshed is not None
        assert refreshed.status == "summarized"


def test_generate_summary_rejects_insufficient_notes_without_fake_summary(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        event = create_earnings_event(
            conn,
            EarningsEventInput(
                ticker="BBCA",
                period="2026-Q2",
                event_date=date(2026, 7, 31),
                source_type="manual",
                notes="",
                now=NOW,
            ),
        )

        with pytest.raises(ValueError, match="insufficient_data"):
            generate_earnings_summary(conn, event.id, generated_at=NOW)

        assert list_earnings_summaries(conn) == []


def test_update_event_notes_enables_summary(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        event = create_earnings_event(
            conn,
            EarningsEventInput(
                ticker="BBCA",
                period="2026-Q2",
                event_date=date(2026, 7, 31),
                source_type="manual",
                notes="",
                now=NOW,
            ),
        )

        updated = update_earnings_event_notes(
            conn,
            event.id,
            notes="Manual notes added after the release call. Revenue grew and cost pressure remains a caveat.",
            now=NOW,
        )
        summary = generate_earnings_summary(conn, event.id, generated_at=NOW)

        assert updated is not None
        assert updated.notes
        assert summary.confidence_status == "manual_only"


def _db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "earnings.duckdb"))
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
    return conn
