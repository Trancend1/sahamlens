"""DuckDB persistence for local alert rules, evaluations, and events."""

from __future__ import annotations

import json
from datetime import datetime

import duckdb
from packages.core.alerts.models import (
    AlertDeliveryAttempt,
    AlertDeliveryStatus,
    AlertEvaluation,
    AlertEvent,
    AlertEventStatus,
    AlertRule,
    AlertRuleInput,
)


def create_alert_rule(
    conn: duckdb.DuckDBPyConnection,
    rule_input: AlertRuleInput,
    *,
    rule_id: str | None = None,
) -> AlertRule:
    from uuid import uuid4

    rule = AlertRule(
        id=rule_id or f"alert-rule-{uuid4().hex}",
        name=rule_input.name,
        description=rule_input.description,
        rule_type=rule_input.rule_type,
        ticker=rule_input.ticker,
        parameters=rule_input.parameters,
        is_active=True,
        created_at=rule_input.now,
        updated_at=rule_input.now,
    )
    conn.execute(
        """
        INSERT INTO alert_rules
            (id, name, description, rule_type, ticker, parameters_json,
             is_active, created_at, updated_at, archived_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            rule.id,
            rule.name,
            rule.description,
            rule.rule_type,
            rule.ticker,
            json.dumps(rule.parameters, sort_keys=True),
            int(rule.is_active),
            rule.created_at.isoformat(),
            rule.updated_at.isoformat(),
            rule.archived_at.isoformat() if rule.archived_at else None,
        ],
    )
    return rule


def list_alert_rules(
    conn: duckdb.DuckDBPyConnection,
    *,
    active_only: bool = False,
    include_archived: bool = True,
) -> list[AlertRule]:
    clauses: list[str] = []
    if active_only:
        clauses.append("is_active = 1")
    if not include_archived:
        clauses.append("archived_at IS NULL")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"""
        SELECT id, name, description, rule_type, ticker, parameters_json,
               is_active, created_at, updated_at, archived_at
        FROM alert_rules
        {where}
        ORDER BY created_at, id
        """
    ).fetchall()
    return [_row_to_rule(row) for row in rows]


def get_alert_rule(
    conn: duckdb.DuckDBPyConnection,
    rule_id: str,
) -> AlertRule | None:
    row = conn.execute(
        """
        SELECT id, name, description, rule_type, ticker, parameters_json,
               is_active, created_at, updated_at, archived_at
        FROM alert_rules
        WHERE id = ?
        """,
        [rule_id],
    ).fetchone()
    return _row_to_rule(row) if row else None


def pause_alert_rule(
    conn: duckdb.DuckDBPyConnection,
    rule_id: str,
    *,
    now: datetime,
) -> AlertRule | None:
    conn.execute(
        """
        UPDATE alert_rules
        SET is_active = 0, updated_at = ?
        WHERE id = ? AND archived_at IS NULL
        """,
        [now.isoformat(), rule_id],
    )
    return get_alert_rule(conn, rule_id)


def archive_alert_rule(
    conn: duckdb.DuckDBPyConnection,
    rule_id: str,
    *,
    now: datetime,
) -> AlertRule | None:
    conn.execute(
        """
        UPDATE alert_rules
        SET is_active = 0, updated_at = ?, archived_at = COALESCE(archived_at, ?)
        WHERE id = ?
        """,
        [now.isoformat(), now.isoformat(), rule_id],
    )
    return get_alert_rule(conn, rule_id)


def insert_alert_evaluation(
    conn: duckdb.DuckDBPyConnection,
    evaluation: AlertEvaluation,
) -> AlertEvaluation:
    conn.execute(
        """
        INSERT INTO alert_evaluations
            (id, rule_id, evaluated_at, status, reason, data_freshness_status,
             confidence_status, matched, details_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            evaluation.id,
            evaluation.rule_id,
            evaluation.evaluated_at.isoformat(),
            evaluation.status,
            evaluation.reason,
            evaluation.data_freshness_status,
            evaluation.confidence_status,
            int(evaluation.matched),
            json.dumps(evaluation.details, sort_keys=True),
        ],
    )
    return evaluation


def insert_alert_event(
    conn: duckdb.DuckDBPyConnection,
    event: AlertEvent,
) -> AlertEvent:
    conn.execute(
        """
        INSERT INTO alert_events
            (id, rule_id, evaluation_id, ticker, event_type, severity, title,
             message, status, created_at, acknowledged_at, dismissed_at,
             false_positive_at, resolved_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            event.id,
            event.rule_id,
            event.evaluation_id,
            event.ticker,
            event.event_type,
            event.severity,
            event.title,
            event.message,
            event.status,
            event.created_at.isoformat(),
            event.acknowledged_at.isoformat() if event.acknowledged_at else None,
            event.dismissed_at.isoformat() if event.dismissed_at else None,
            event.false_positive_at.isoformat() if event.false_positive_at else None,
            event.resolved_at.isoformat() if event.resolved_at else None,
            event.notes,
        ],
    )
    return event


def insert_alert_delivery_attempt(
    conn: duckdb.DuckDBPyConnection,
    attempt: AlertDeliveryAttempt,
) -> AlertDeliveryAttempt:
    conn.execute(
        """
        INSERT INTO alert_delivery_attempts
            (id, event_id, channel, status, attempted_at, error_code,
             error_message, redacted_details_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            attempt.id,
            attempt.event_id,
            attempt.channel,
            attempt.status,
            attempt.attempted_at.isoformat(),
            attempt.error_code,
            attempt.error_message,
            json.dumps(attempt.redacted_details, sort_keys=True),
        ],
    )
    return attempt


def list_alert_delivery_attempts(
    conn: duckdb.DuckDBPyConnection,
    *,
    event_id: str | None = None,
    status: AlertDeliveryStatus | None = None,
    limit: int | None = None,
) -> list[AlertDeliveryAttempt]:
    clauses: list[str] = []
    params: list[object] = []
    if event_id is not None:
        clauses.append("event_id = ?")
        params.append(event_id)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    limit_sql = ""
    if limit is not None:
        limit_sql = "LIMIT ?"
        params.append(limit)
    rows = conn.execute(
        f"""
        SELECT id, event_id, channel, status, attempted_at, error_code,
               error_message, redacted_details_json
        FROM alert_delivery_attempts
        {where}
        ORDER BY attempted_at DESC, id
        {limit_sql}
        """,
        params,
    ).fetchall()
    return [_row_to_delivery_attempt(row) for row in rows]


def list_alert_events(
    conn: duckdb.DuckDBPyConnection,
    *,
    status: AlertEventStatus | None = None,
    limit: int | None = None,
) -> list[AlertEvent]:
    where = ""
    params: list[object] = []
    if status is not None:
        where = "WHERE status = ?"
        params.append(status)
    limit_sql = ""
    if limit is not None:
        limit_sql = "LIMIT ?"
        params.append(limit)
    rows = conn.execute(
        f"""
        SELECT id, rule_id, evaluation_id, ticker, event_type, severity, title,
               message, status, created_at, acknowledged_at, dismissed_at,
               false_positive_at, resolved_at, notes
        FROM alert_events
        {where}
        ORDER BY created_at DESC, id
        {limit_sql}
        """,
        params,
    ).fetchall()
    return [_row_to_event(row) for row in rows]


def get_alert_event(
    conn: duckdb.DuckDBPyConnection,
    event_id: str,
) -> AlertEvent | None:
    row = conn.execute(
        """
        SELECT id, rule_id, evaluation_id, ticker, event_type, severity, title,
               message, status, created_at, acknowledged_at, dismissed_at,
               false_positive_at, resolved_at, notes
        FROM alert_events
        WHERE id = ?
        """,
        [event_id],
    ).fetchone()
    return _row_to_event(row) if row else None


def acknowledge_alert_event(
    conn: duckdb.DuckDBPyConnection,
    event_id: str,
    *,
    now: datetime,
) -> AlertEvent | None:
    conn.execute(
        """
        UPDATE alert_events
        SET status = 'acknowledged', acknowledged_at = COALESCE(acknowledged_at, ?)
        WHERE id = ? AND status != 'marked_false_positive'
        """,
        [now.isoformat(), event_id],
    )
    return get_alert_event(conn, event_id)


def dismiss_alert_event(
    conn: duckdb.DuckDBPyConnection,
    event_id: str,
    *,
    now: datetime,
) -> AlertEvent | None:
    conn.execute(
        """
        UPDATE alert_events
        SET status = 'dismissed', dismissed_at = COALESCE(dismissed_at, ?)
        WHERE id = ? AND status != 'marked_false_positive'
        """,
        [now.isoformat(), event_id],
    )
    return get_alert_event(conn, event_id)


def mark_alert_event_false_positive(
    conn: duckdb.DuckDBPyConnection,
    event_id: str,
    *,
    notes: str | None = None,
    now: datetime,
) -> AlertEvent | None:
    existing = get_alert_event(conn, event_id)
    if existing is None:
        return None
    if existing.status == "marked_false_positive":
        return existing
    conn.execute(
        """
        UPDATE alert_events
        SET status = 'marked_false_positive',
            false_positive_at = COALESCE(false_positive_at, ?),
            notes = COALESCE(?, notes)
        WHERE id = ?
        """,
        [now.isoformat(), notes, event_id],
    )
    return get_alert_event(conn, event_id)


def resolve_alert_event(
    conn: duckdb.DuckDBPyConnection,
    event_id: str,
    *,
    now: datetime,
) -> AlertEvent | None:
    conn.execute(
        """
        UPDATE alert_events
        SET status = 'resolved', resolved_at = COALESCE(resolved_at, ?)
        WHERE id = ? AND status != 'marked_false_positive'
        """,
        [now.isoformat(), event_id],
    )
    return get_alert_event(conn, event_id)


def _row_to_rule(row: tuple[object, ...]) -> AlertRule:
    return AlertRule.model_validate(
        {
            "id": str(row[0]),
            "name": str(row[1]),
            "description": str(row[2]),
            "rule_type": str(row[3]),
            "ticker": str(row[4]),
            "parameters": json.loads(str(row[5])),
            "is_active": bool(row[6]),
            "created_at": datetime.fromisoformat(str(row[7])),
            "updated_at": datetime.fromisoformat(str(row[8])),
            "archived_at": _optional_datetime(row[9]),
        }
    )


def _row_to_event(row: tuple[object, ...]) -> AlertEvent:
    return AlertEvent.model_validate(
        {
            "id": str(row[0]),
            "rule_id": str(row[1]),
            "evaluation_id": str(row[2]),
            "ticker": str(row[3]),
            "event_type": str(row[4]),
            "severity": str(row[5]),
            "title": str(row[6]),
            "message": str(row[7]),
            "status": str(row[8]),
            "created_at": datetime.fromisoformat(str(row[9])),
            "acknowledged_at": _optional_datetime(row[10]),
            "dismissed_at": _optional_datetime(row[11]),
            "false_positive_at": _optional_datetime(row[12]),
            "resolved_at": _optional_datetime(row[13]),
            "notes": _optional_str(row[14]),
        }
    )


def _row_to_delivery_attempt(row: tuple[object, ...]) -> AlertDeliveryAttempt:
    return AlertDeliveryAttempt.model_validate(
        {
            "id": str(row[0]),
            "event_id": str(row[1]),
            "channel": str(row[2]),
            "status": str(row[3]),
            "attempted_at": datetime.fromisoformat(str(row[4])),
            "error_code": _optional_str(row[5]),
            "error_message": _optional_str(row[6]),
            "redacted_details": json.loads(str(row[7])),
        }
    )


def _optional_datetime(value: object) -> datetime | None:
    return datetime.fromisoformat(str(value)) if value is not None else None


def _optional_str(value: object) -> str | None:
    return str(value) if value is not None else None
