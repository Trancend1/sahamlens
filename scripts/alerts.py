"""Local alert lifecycle CLI for V1-S6.

Examples:
  uv run python -m scripts.alerts --json rules list
  uv run python -m scripts.alerts --json rules create --name "BBCA review" --rule-type price_above --ticker BBCA --params '{"threshold":9000}'
  uv run python -m scripts.alerts --json evaluate
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import duckdb
from packages.core.alerts import (
    AlertRuleInput,
    acknowledge_alert_event,
    archive_alert_rule,
    create_alert_rule,
    dismiss_alert_event,
    evaluate_active_alert_rules,
    get_telegram_status,
    list_alert_events,
    list_alert_rules,
    mark_alert_event_false_positive,
    pause_alert_rule,
    send_alert_event_to_telegram,
)
from packages.core.runtime import get_runtime_status
from packages.core.schemas.repository import open_connection
from pydantic import ValidationError

EXIT_OK = 0
EXIT_FAILED = 3
ALERT_REQUIRED_TABLES = {
    "alert_rules",
    "alert_evaluations",
    "alert_events",
    "alert_delivery_attempts",
}


def cmd_rules_list(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    with open_connection(args.db) as conn:
        items = [item.model_dump(mode="json") for item in list_alert_rules(conn)]
    _emit(_ok(items=items), as_json=args.json)
    return EXIT_OK


def cmd_rules_create(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    try:
        params = _parse_json_object(args.params)
        rule_input = AlertRuleInput(
            name=args.name,
            description=args.description or args.name,
            rule_type=args.rule_type,
            ticker=args.ticker,
            parameters=params,
        )
        with open_connection(args.db) as conn:
            item = create_alert_rule(conn, rule_input).model_dump(mode="json")
    except (ValueError, ValidationError) as exc:
        _emit(_error("invalid_input", _clean_error(exc)), as_json=args.json)
        return EXIT_FAILED
    except duckdb.Error as exc:
        _emit(_duckdb_error(exc), as_json=args.json)
        return EXIT_FAILED
    _emit(_ok(item=item, status="created"), as_json=args.json)
    return EXIT_OK


def cmd_rules_pause(args: argparse.Namespace) -> int:
    return _rule_mutation(args, action="pause")


def cmd_rules_archive(args: argparse.Namespace) -> int:
    return _rule_mutation(args, action="archive")


def cmd_evaluate(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    try:
        with open_connection(args.db) as conn:
            result = evaluate_active_alert_rules(conn)
    except duckdb.Error as exc:
        _emit(_duckdb_error(exc), as_json=args.json)
        return EXIT_FAILED
    _emit(_ok(item=result.model_dump(mode="json"), status="evaluated"), as_json=args.json)
    return EXIT_OK


def cmd_events_list(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    with open_connection(args.db) as conn:
        items = [
            item.model_dump(mode="json")
            for item in list_alert_events(conn, status=args.status, limit=args.limit)
        ]
    _emit(_ok(items=items), as_json=args.json)
    return EXIT_OK


def cmd_events_acknowledge(args: argparse.Namespace) -> int:
    return _event_mutation(args, action="acknowledge")


def cmd_events_dismiss(args: argparse.Namespace) -> int:
    return _event_mutation(args, action="dismiss")


def cmd_events_mark_false_positive(args: argparse.Namespace) -> int:
    return _event_mutation(args, action="mark_false_positive")


def cmd_telegram_status(args: argparse.Namespace) -> int:
    status = get_telegram_status()
    item = status.model_dump(mode="json")
    payload = _ok(item=item, status=status.status, warnings=status.warnings)
    payload.update(
        {
            "enabled": status.enabled,
            "configured": status.configured,
            "bot_token_configured": status.bot_token_configured,
            "chat_id_configured": status.chat_id_configured,
        }
    )
    _emit(payload, as_json=args.json)
    return EXIT_OK


def cmd_telegram_send(args: argparse.Namespace) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    try:
        with open_connection(args.db) as conn:
            result = send_alert_event_to_telegram(conn, args.event_id)
    except duckdb.Error as exc:
        _emit(_duckdb_error(exc), as_json=args.json)
        return EXIT_FAILED
    status_code = EXIT_OK if result.status == "skipped_not_configured" or result.ok else EXIT_FAILED
    _emit(
        {
            "ok": result.ok or result.status == "skipped_not_configured",
            "status": result.status,
            "item": result.model_dump(mode="json"),
            "warnings": result.warnings,
            "errors": result.errors,
            "recommended_commands": result.recommended_commands,
        },
        as_json=args.json,
    )
    return status_code


def _rule_mutation(args: argparse.Namespace, *, action: str) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    now = datetime.now(UTC)
    with open_connection(args.db) as conn:
        item = (
            pause_alert_rule(conn, args.rule_id, now=now)
            if action == "pause"
            else archive_alert_rule(conn, args.rule_id, now=now)
        )
    if item is None:
        _emit(_error("not_found", "Alert rule was not found."), as_json=args.json)
        return EXIT_FAILED
    _emit(_ok(item=item.model_dump(mode="json"), status=action), as_json=args.json)
    return EXIT_OK


def _event_mutation(args: argparse.Namespace, *, action: str) -> int:
    readiness = _runtime_ready(args.db)
    if readiness is not None:
        _emit(readiness, as_json=args.json)
        return EXIT_FAILED
    now = datetime.now(UTC)
    with open_connection(args.db) as conn:
        if action == "acknowledge":
            item = acknowledge_alert_event(conn, args.event_id, now=now)
        elif action == "dismiss":
            item = dismiss_alert_event(conn, args.event_id, now=now)
        else:
            item = mark_alert_event_false_positive(
                conn,
                args.event_id,
                notes=args.notes,
                now=now,
            )
    if item is None:
        _emit(_error("not_found", "Alert event was not found."), as_json=args.json)
        return EXIT_FAILED
    _emit(_ok(item=item.model_dump(mode="json"), status=action), as_json=args.json)
    return EXIT_OK


def _runtime_ready(db_path: str | None) -> dict[str, Any] | None:
    status = get_runtime_status(db_path)
    missing_alert_tables = sorted(set(status.missing_tables) & ALERT_REQUIRED_TABLES)
    if status.schema_status == "ready" and not missing_alert_tables:
        return None
    code = "schema_stale" if status.pending_migrations else "missing_table"
    message = (
        "Local alert schema is not ready. Run migration before using alerts."
        if code == "schema_stale"
        else f"Missing alert table(s): {', '.join(missing_alert_tables)}."
    )
    return _error(
        code,
        message,
        status="schema_stale",
        details={
            "pending_migrations": status.pending_migrations,
            "missing_tables": missing_alert_tables or status.missing_tables,
        },
        recommended_commands=["uv run python -m scripts.migrate"],
    )


def _parse_json_object(raw: str) -> dict[str, Any]:
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("--params must be a JSON object")
    return parsed


def _ok(
    *,
    status: str = "ok",
    item: object | None = None,
    items: Sequence[object] | None = None,
    warnings: Sequence[object] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": True,
        "status": status,
        "warnings": list(warnings or []),
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
            "Local alert schema is not ready. Run migration before using alerts.",
            status="schema_stale",
            recommended_commands=["uv run python -m scripts.migrate"],
        )
    return _error("command_failed", "The local alert command could not complete.")


def _clean_error(exc: Exception) -> str:
    message = str(exc).splitlines()[0]
    return message[:240]


def _emit(payload: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload))
        return
    print(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SahamLens local alerts CLI.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")

    sub = parser.add_subparsers(dest="cmd", required=True)

    rules = sub.add_parser("rules", help="Manage alert rules.")
    rules_sub = rules.add_subparsers(dest="rules_cmd", required=True)

    p_rules_list = rules_sub.add_parser("list", help="List alert rules.")
    p_rules_list.set_defaults(func=cmd_rules_list)

    p_rules_create = rules_sub.add_parser("create", help="Create alert rule.")
    p_rules_create.add_argument("--name", required=True)
    p_rules_create.add_argument("--description", default="")
    p_rules_create.add_argument("--rule-type", required=True)
    p_rules_create.add_argument("--ticker", required=True)
    p_rules_create.add_argument("--params", required=True)
    p_rules_create.set_defaults(func=cmd_rules_create)

    p_rules_pause = rules_sub.add_parser("pause", help="Pause alert rule.")
    p_rules_pause.add_argument("--rule-id", required=True)
    p_rules_pause.set_defaults(func=cmd_rules_pause)

    p_rules_archive = rules_sub.add_parser("archive", help="Archive alert rule.")
    p_rules_archive.add_argument("--rule-id", required=True)
    p_rules_archive.set_defaults(func=cmd_rules_archive)

    p_evaluate = sub.add_parser("evaluate", help="Evaluate active alert rules.")
    p_evaluate.set_defaults(func=cmd_evaluate)

    events = sub.add_parser("events", help="Review alert events.")
    events_sub = events.add_subparsers(dest="events_cmd", required=True)

    p_events_list = events_sub.add_parser("list", help="List alert events.")
    p_events_list.add_argument("--status", default=None)
    p_events_list.add_argument("--limit", type=int, default=None)
    p_events_list.set_defaults(func=cmd_events_list)

    p_ack = events_sub.add_parser("acknowledge", help="Acknowledge alert event.")
    p_ack.add_argument("--event-id", required=True)
    p_ack.set_defaults(func=cmd_events_acknowledge)

    p_dismiss = events_sub.add_parser("dismiss", help="Dismiss alert event.")
    p_dismiss.add_argument("--event-id", required=True)
    p_dismiss.set_defaults(func=cmd_events_dismiss)

    p_fp = events_sub.add_parser(
        "mark-false-positive",
        help="Mark alert event as false positive.",
    )
    p_fp.add_argument("--event-id", required=True)
    p_fp.add_argument("--notes", default=None)
    p_fp.set_defaults(func=cmd_events_mark_false_positive)

    telegram = sub.add_parser("telegram", help="Inspect optional Telegram delivery.")
    telegram_sub = telegram.add_subparsers(dest="telegram_cmd", required=True)
    p_tg_status = telegram_sub.add_parser("status", help="Show Telegram delivery status.")
    p_tg_status.set_defaults(func=cmd_telegram_status)

    p_tg_send = telegram_sub.add_parser("send", help="Send alert event to Telegram.")
    p_tg_send.add_argument("--event-id", required=True)
    p_tg_send.set_defaults(func=cmd_telegram_send)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
