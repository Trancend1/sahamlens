"""DuckDB persistence for simple strategy rules and evaluations."""

from __future__ import annotations

import json
from datetime import datetime

import duckdb
from packages.core.strategy.models import (
    StrategyRule,
    StrategyRuleEvaluation,
    StrategyRuleViolation,
)


def upsert_strategy_rule(conn: duckdb.DuckDBPyConnection, rule: StrategyRule) -> int:
    conn.execute(
        """
        INSERT INTO strategy_rules
            (rule_id, name, description, rule_category, required_fields,
             violation_code, needs_data_behavior, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (rule_id) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            rule_category = EXCLUDED.rule_category,
            required_fields = EXCLUDED.required_fields,
            violation_code = EXCLUDED.violation_code,
            needs_data_behavior = EXCLUDED.needs_data_behavior,
            is_active = EXCLUDED.is_active,
            updated_at = EXCLUDED.updated_at
        """,
        [
            rule.rule_id,
            rule.name,
            rule.description,
            rule.rule_category,
            json.dumps(rule.required_fields),
            rule.violation_code,
            rule.needs_data_behavior,
            int(rule.is_active),
            rule.created_at.isoformat(),
            rule.updated_at.isoformat(),
        ],
    )
    return 1


def upsert_strategy_rules(conn: duckdb.DuckDBPyConnection, rules: list[StrategyRule]) -> int:
    for rule in rules:
        upsert_strategy_rule(conn, rule)
    return len(rules)


def list_strategy_rules(
    conn: duckdb.DuckDBPyConnection,
    *,
    active_only: bool = False,
) -> list[StrategyRule]:
    where = "WHERE is_active = 1" if active_only else ""
    rows = conn.execute(
        f"""
        SELECT rule_id, name, description, rule_category, required_fields,
               violation_code, needs_data_behavior, is_active, created_at, updated_at
        FROM strategy_rules
        {where}
        ORDER BY rule_id
        """
    ).fetchall()
    return [_row_to_rule(row) for row in rows]


def upsert_strategy_rule_evaluations(
    conn: duckdb.DuckDBPyConnection,
    evaluations: list[StrategyRuleEvaluation],
) -> int:
    for evaluation in evaluations:
        conn.execute(
            """
            INSERT INTO strategy_rule_evaluations
                (evaluation_id, review_id, rule_id, journal_id, symbol,
                 evaluation_status, evaluated_at, evidence, caveats, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (evaluation_id) DO UPDATE SET
                review_id = EXCLUDED.review_id,
                rule_id = EXCLUDED.rule_id,
                journal_id = EXCLUDED.journal_id,
                symbol = EXCLUDED.symbol,
                evaluation_status = EXCLUDED.evaluation_status,
                evaluated_at = EXCLUDED.evaluated_at,
                evidence = EXCLUDED.evidence,
                caveats = EXCLUDED.caveats,
                reason = EXCLUDED.reason
            """,
            [
                evaluation.evaluation_id,
                evaluation.review_id,
                evaluation.rule_id,
                evaluation.journal_id,
                evaluation.symbol,
                evaluation.evaluation_status,
                evaluation.evaluated_at.isoformat(),
                json.dumps(evaluation.evidence),
                json.dumps(evaluation.caveats),
                evaluation.reason,
            ],
        )
        conn.execute(
            "DELETE FROM strategy_rule_violations WHERE evaluation_id = ?",
            [evaluation.evaluation_id],
        )
        for violation in evaluation.violations:
            _insert_violation(conn, violation)
    return len(evaluations)


def list_strategy_rule_evaluations(
    conn: duckdb.DuckDBPyConnection,
    *,
    review_id: str | None = None,
) -> list[StrategyRuleEvaluation]:
    where = "WHERE review_id = ?" if review_id else ""
    params = [review_id] if review_id else []
    rows = conn.execute(
        f"""
        SELECT evaluation_id, review_id, rule_id, journal_id, symbol,
               evaluation_status, evaluated_at, evidence, caveats, reason
        FROM strategy_rule_evaluations
        {where}
        ORDER BY evaluated_at DESC, rule_id, journal_id
        """,
        params,
    ).fetchall()
    return [_row_to_evaluation(conn, row) for row in rows]


def _insert_violation(
    conn: duckdb.DuckDBPyConnection,
    violation: StrategyRuleViolation,
) -> None:
    conn.execute(
        """
        INSERT INTO strategy_rule_violations
            (violation_id, evaluation_id, review_id, rule_id, journal_id, symbol,
             violation_code, violation_detail, evidence, caveats, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (violation_id) DO UPDATE SET
            evaluation_id = EXCLUDED.evaluation_id,
            review_id = EXCLUDED.review_id,
            rule_id = EXCLUDED.rule_id,
            journal_id = EXCLUDED.journal_id,
            symbol = EXCLUDED.symbol,
            violation_code = EXCLUDED.violation_code,
            violation_detail = EXCLUDED.violation_detail,
            evidence = EXCLUDED.evidence,
            caveats = EXCLUDED.caveats,
            created_at = EXCLUDED.created_at
        """,
        [
            violation.violation_id,
            violation.evaluation_id,
            violation.review_id,
            violation.rule_id,
            violation.journal_id,
            violation.symbol,
            violation.violation_code,
            violation.violation_detail,
            json.dumps(violation.evidence),
            json.dumps(violation.caveats),
            violation.created_at.isoformat(),
        ],
    )


def _row_to_rule(row: tuple[object, ...]) -> StrategyRule:
    return StrategyRule.model_validate(
        {
            "rule_id": str(row[0]),
            "name": str(row[1]),
            "description": str(row[2]),
            "rule_category": str(row[3]),
            "required_fields": _json_list(row[4]),
            "violation_code": str(row[5]),
            "needs_data_behavior": str(row[6]),
            "is_active": bool(row[7]),
            "created_at": datetime.fromisoformat(str(row[8])),
            "updated_at": datetime.fromisoformat(str(row[9])),
        }
    )


def _row_to_evaluation(
    conn: duckdb.DuckDBPyConnection,
    row: tuple[object, ...],
) -> StrategyRuleEvaluation:
    evaluation_id = str(row[0])
    violations = conn.execute(
        """
        SELECT violation_id, evaluation_id, review_id, rule_id, journal_id, symbol,
               violation_code, violation_detail, evidence, caveats, created_at
        FROM strategy_rule_violations
        WHERE evaluation_id = ?
        ORDER BY violation_code
        """,
        [evaluation_id],
    ).fetchall()
    return StrategyRuleEvaluation.model_validate(
        {
            "evaluation_id": evaluation_id,
            "review_id": _optional_str(row[1]),
            "rule_id": str(row[2]),
            "journal_id": int(row[3]) if row[3] is not None else None,
            "symbol": _optional_str(row[4]),
            "evaluation_status": str(row[5]),
            "evaluated_at": datetime.fromisoformat(str(row[6])),
            "evidence": _json_list(row[7]),
            "caveats": _json_list(row[8]),
            "reason": str(row[9]),
            "violations": [_row_to_violation(violation) for violation in violations],
        }
    )


def _row_to_violation(row: tuple[object, ...]) -> StrategyRuleViolation:
    return StrategyRuleViolation.model_validate(
        {
            "violation_id": str(row[0]),
            "evaluation_id": str(row[1]),
            "review_id": _optional_str(row[2]),
            "rule_id": str(row[3]),
            "journal_id": int(row[4]) if row[4] is not None else None,
            "symbol": _optional_str(row[5]),
            "violation_code": str(row[6]),
            "violation_detail": str(row[7]),
            "evidence": _json_list(row[8]),
            "caveats": _json_list(row[9]),
            "created_at": datetime.fromisoformat(str(row[10])),
        }
    )


def _json_list(value: object) -> list[str]:
    parsed = json.loads(str(value))
    if not isinstance(parsed, list):
        raise ValueError("expected JSON list")
    return [str(item) for item in parsed]


def _optional_str(value: object) -> str | None:
    return str(value) if value is not None else None
