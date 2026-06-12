"""Manual-first earnings workflow CLI for V1-S6."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import duckdb
from packages.core.earnings import (
    EarningsEventInput,
    archive_earnings_event,
    create_earnings_event,
    generate_earnings_summary,
    get_earnings_event,
    list_earnings_events,
    list_earnings_summaries,
    update_earnings_event_notes,
)
from packages.core.runtime import get_runtime_status
from packages.core.schemas.repository import open_connection
from pydantic import ValidationError

EXIT_OK = 0
EXIT_FAILED = 3
EARNINGS_REQUIRED_TABLES = {"earnings_events", "earnings_summaries"}


def cmd_events_list(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    with open_connection(args.db, read_only=True) as conn:
        items = [
            item.model_dump(mode="json")
            for item in list_earnings_events(conn, include_archived=args.include_archived)
        ]
    _emit(_ok(items=items), as_json=args.json)
    return EXIT_OK


def cmd_events_create(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    try:
        event_input = EarningsEventInput(
            ticker=args.ticker,
            period=args.period,
            event_date=args.event_date,
            source_type=args.source_type,
            source_ref=args.source_ref,
            notes=args.notes,
        )
        with open_connection(args.db) as conn:
            item = create_earnings_event(conn, event_input).model_dump(mode="json")
    except (ValueError, ValidationError) as exc:
        _emit(_error("invalid_input", _clean_error(exc)), as_json=args.json)
        return EXIT_FAILED
    except duckdb.Error as exc:
        _emit(_duckdb_error(exc), as_json=args.json)
        return EXIT_FAILED
    _emit(_ok(item=item, status="created"), as_json=args.json)
    return EXIT_OK


def cmd_events_detail(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    with open_connection(args.db, read_only=True) as conn:
        item = get_earnings_event(conn, args.event_id)
    if item is None:
        _emit(_error("not_found", "Earnings event was not found."), as_json=args.json)
        return EXIT_FAILED
    _emit(_ok(item=item.model_dump(mode="json")), as_json=args.json)
    return EXIT_OK


def cmd_events_update_notes(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    try:
        with open_connection(args.db) as conn:
            item = update_earnings_event_notes(
                conn,
                args.event_id,
                notes=args.notes,
                now=datetime.now(UTC),
            )
    except ValueError as exc:
        _emit(_error("invalid_input", _clean_error(exc)), as_json=args.json)
        return EXIT_FAILED
    if item is None:
        _emit(_error("not_found", "Earnings event was not found."), as_json=args.json)
        return EXIT_FAILED
    _emit(_ok(item=item.model_dump(mode="json"), status="updated"), as_json=args.json)
    return EXIT_OK


def cmd_events_archive(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    with open_connection(args.db) as conn:
        item = archive_earnings_event(conn, args.event_id, now=datetime.now(UTC))
    if item is None:
        _emit(_error("not_found", "Earnings event was not found."), as_json=args.json)
        return EXIT_FAILED
    _emit(_ok(item=item.model_dump(mode="json"), status="archived"), as_json=args.json)
    return EXIT_OK


def cmd_summary_generate(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    try:
        with open_connection(args.db) as conn:
            item = generate_earnings_summary(conn, args.event_id).model_dump(mode="json")
    except ValueError as exc:
        message = _clean_error(exc)
        if "insufficient_data" in message:
            _emit(
                _error(
                    "insufficient_data",
                    "Add manual notes or source context before generating a summary.",
                    status="insufficient_data",
                    recommended_commands=[],
                ),
                as_json=args.json,
            )
            return EXIT_FAILED
        if "not_found" in message:
            _emit(_error("not_found", "Earnings event was not found."), as_json=args.json)
            return EXIT_FAILED
        _emit(_error("invalid_input", message), as_json=args.json)
        return EXIT_FAILED
    except duckdb.Error as exc:
        _emit(_duckdb_error(exc), as_json=args.json)
        return EXIT_FAILED
    _emit(_ok(item=item, status="generated"), as_json=args.json)
    return EXIT_OK


def cmd_summaries_list(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    with open_connection(args.db, read_only=True) as conn:
        items = [item.model_dump(mode="json") for item in list_earnings_summaries(conn)]
    _emit(_ok(items=items), as_json=args.json)
    return EXIT_OK


def _runtime_ready(db_path: str | None) -> dict[str, Any] | None:
    status = get_runtime_status(db_path)
    missing_earnings_tables = sorted(set(status.missing_tables) & EARNINGS_REQUIRED_TABLES)
    if status.schema_status == "ready" and not missing_earnings_tables:
        return None
    code = "schema_stale" if status.pending_migrations else "missing_table"
    message = (
        "Local earnings schema is not ready. Run migration before using earnings."
        if code == "schema_stale"
        else f"Missing earnings table(s): {', '.join(missing_earnings_tables)}."
    )
    return _error(
        code,
        message,
        status="schema_stale",
        details={
            "pending_migrations": status.pending_migrations,
            "missing_tables": missing_earnings_tables or status.missing_tables,
        },
        recommended_commands=["uv run python -m scripts.migrate"],
    )


def _ok(
    *,
    status: str = "ok",
    item: object | None = None,
    items: Sequence[object] | None = None,
    warnings: list[object] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": True,
        "status": status,
        "warnings": warnings or [],
        "errors": [],
        "recommended_commands": [],
    }
    if item is not None:
        payload["item"] = item
    if items is not None:
        payload["items"] = list(items)
    return payload


def _error(
    code: str,
    message: str,
    *,
    status: str = "command_failed",
    details: dict[str, Any] | None = None,
    recommended_commands: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "items": [],
        "warnings": [],
        "errors": [
            {
                "code": code,
                "message": message,
                "details": details or {},
            }
        ],
        "recommended_commands": recommended_commands or [],
    }


def _duckdb_error(exc: duckdb.Error) -> dict[str, Any]:
    raw = str(exc)
    if "does not exist" in raw or "no such table" in raw:
        return _error(
            "missing_table",
            "Local earnings schema is not ready. Run migration before using earnings.",
            status="schema_stale",
            recommended_commands=["uv run python -m scripts.migrate"],
        )
    if "lock" in raw.lower() or "locked" in raw.lower() or "IO Error" in raw:
        return _error(
            "db_locked",
            (
                "Local DuckDB file is locked. Close other SahamLens commands using "
                "the same DB, then retry sequentially."
            ),
        )
    return _error("command_failed", "The local earnings command could not complete.")


def _clean_error(exc: Exception) -> str:
    return str(exc).splitlines()[0][:240]


def _emit(payload: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload))
        return
    print(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SahamLens manual earnings CLI.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")

    sub = parser.add_subparsers(dest="cmd", required=True)

    events = sub.add_parser("events", help="Manage earnings events.")
    events_sub = events.add_subparsers(dest="events_cmd", required=True)

    p_events_list = events_sub.add_parser("list", help="List earnings events.")
    p_events_list.add_argument("--include-archived", action="store_true")
    p_events_list.set_defaults(func=cmd_events_list)

    p_events_create = events_sub.add_parser("create", help="Create earnings event.")
    p_events_create.add_argument("--ticker", required=True)
    p_events_create.add_argument("--period", required=True)
    p_events_create.add_argument("--event-date", required=True)
    p_events_create.add_argument("--source-type", default="manual")
    p_events_create.add_argument("--source-ref", default=None)
    p_events_create.add_argument("--notes", default=None)
    p_events_create.set_defaults(func=cmd_events_create)

    p_events_detail = events_sub.add_parser("detail", help="Read earnings event detail.")
    p_events_detail.add_argument("--event-id", required=True)
    p_events_detail.set_defaults(func=cmd_events_detail)

    p_events_notes = events_sub.add_parser("update-notes", help="Update earnings notes.")
    p_events_notes.add_argument("--event-id", required=True)
    p_events_notes.add_argument("--notes", required=True)
    p_events_notes.set_defaults(func=cmd_events_update_notes)

    p_events_archive = events_sub.add_parser("archive", help="Archive earnings event.")
    p_events_archive.add_argument("--event-id", required=True)
    p_events_archive.set_defaults(func=cmd_events_archive)

    summary = sub.add_parser("summary", help="Generate earnings summaries.")
    summary_sub = summary.add_subparsers(dest="summary_cmd", required=True)

    p_summary_generate = summary_sub.add_parser(
        "generate",
        help="Generate caveated summary for an event.",
    )
    p_summary_generate.add_argument("--event-id", required=True)
    p_summary_generate.set_defaults(func=cmd_summary_generate)

    summaries = sub.add_parser("summaries", help="List earnings summaries.")
    summaries_sub = summaries.add_subparsers(dest="summaries_cmd", required=True)
    p_summaries_list = summaries_sub.add_parser("list", help="List summaries.")
    p_summaries_list.set_defaults(func=cmd_summaries_list)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
