"""DuckDB persistence for transparent screener rules, runs, and results."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import duckdb
from packages.core.screener.models import (
    ScreenerCondition,
    ScreenerExclusion,
    ScreenerResult,
    ScreenerRule,
    ScreenerRun,
)


def upsert_screener_rule(conn: duckdb.DuckDBPyConnection, rule: ScreenerRule) -> int:
    conn.execute(
        """
        INSERT INTO screener_rules
            (rule_id, name, description, required_fields, required_source_types,
             min_coverage_tier, allowed_freshness_states, min_fundamental_completeness,
             min_confidence_level, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (rule_id) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            required_fields = EXCLUDED.required_fields,
            required_source_types = EXCLUDED.required_source_types,
            min_coverage_tier = EXCLUDED.min_coverage_tier,
            allowed_freshness_states = EXCLUDED.allowed_freshness_states,
            min_fundamental_completeness = EXCLUDED.min_fundamental_completeness,
            min_confidence_level = EXCLUDED.min_confidence_level,
            is_active = EXCLUDED.is_active,
            updated_at = EXCLUDED.updated_at
        """,
        [
            rule.rule_id,
            rule.name,
            rule.description,
            json.dumps(rule.required_fields),
            json.dumps(rule.required_source_types),
            rule.min_coverage_tier,
            json.dumps(rule.allowed_freshness_states),
            rule.min_fundamental_completeness,
            rule.min_confidence_level,
            int(rule.is_active),
            rule.created_at.isoformat(),
            rule.updated_at.isoformat(),
        ],
    )
    conn.execute("DELETE FROM screener_rule_conditions WHERE rule_id = ?", [rule.rule_id])
    for condition in rule.conditions:
        conn.execute(
            """
            INSERT INTO screener_rule_conditions
                (condition_id, rule_id, field_name, operator, value_json,
                 required_source_type, missing_behavior, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                condition.condition_id,
                rule.rule_id,
                condition.field_name,
                condition.operator,
                json.dumps(condition.value) if condition.value is not None else None,
                condition.required_source_type,
                condition.missing_behavior,
                condition.description,
            ],
        )
    return 1


def get_screener_rule(conn: duckdb.DuckDBPyConnection, rule_id: str) -> ScreenerRule | None:
    row = conn.execute(
        """
        SELECT rule_id, name, description, required_fields, required_source_types,
               min_coverage_tier, allowed_freshness_states, min_fundamental_completeness,
               min_confidence_level, is_active, created_at, updated_at
        FROM screener_rules
        WHERE rule_id = ?
        """,
        [rule_id],
    ).fetchone()
    if row is None:
        return None
    conditions = _list_conditions(conn, rule_id)
    return _row_to_rule(row, conditions)


def upsert_screener_run(conn: duckdb.DuckDBPyConnection, run: ScreenerRun) -> int:
    upsert_screener_rule(conn, run.rule)
    conn.execute(
        """
        INSERT INTO screener_runs
            (run_id, rule_id, started_at, completed_at, status, universe_count,
             included_count, excluded_count, data_quality_snapshot, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (run_id) DO UPDATE SET
            rule_id = EXCLUDED.rule_id,
            started_at = EXCLUDED.started_at,
            completed_at = EXCLUDED.completed_at,
            status = EXCLUDED.status,
            universe_count = EXCLUDED.universe_count,
            included_count = EXCLUDED.included_count,
            excluded_count = EXCLUDED.excluded_count,
            data_quality_snapshot = EXCLUDED.data_quality_snapshot,
            notes = EXCLUDED.notes
        """,
        [
            run.run_id,
            run.rule.rule_id,
            run.started_at.isoformat(),
            run.completed_at.isoformat() if run.completed_at else None,
            run.status,
            run.universe_count,
            run.included_count,
            run.excluded_count,
            json.dumps(run.data_quality_snapshot, sort_keys=True),
            run.notes,
        ],
    )
    conn.execute("DELETE FROM screener_result_exclusions WHERE run_id = ?", [run.run_id])
    conn.execute("DELETE FROM screener_results WHERE run_id = ?", [run.run_id])
    for result in run.results:
        _insert_result(conn, result)
    return 1


def list_screener_results(
    conn: duckdb.DuckDBPyConnection,
    *,
    run_id: str,
) -> list[ScreenerResult]:
    rows = conn.execute(
        """
        SELECT run_id, symbol, result_status, coverage_tier, lifecycle_status,
               freshness_state, completeness_state, confidence_level, matched_conditions,
               failed_conditions, missing_fields, exclusion_reasons, caveats, explanation,
               evaluated_at
        FROM screener_results
        WHERE run_id = ?
        ORDER BY symbol
        """,
        [run_id],
    ).fetchall()
    return [_row_to_result(conn, row) for row in rows]


def _insert_result(conn: duckdb.DuckDBPyConnection, result: ScreenerResult) -> None:
    conn.execute(
        """
        INSERT INTO screener_results
            (run_id, symbol, result_status, coverage_tier, lifecycle_status,
             freshness_state, completeness_state, confidence_level, matched_conditions,
             failed_conditions, missing_fields, exclusion_reasons, caveats, explanation,
             evaluated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            result.run_id,
            result.symbol,
            result.result_status,
            result.coverage_tier,
            result.lifecycle_status,
            result.freshness_state,
            result.completeness_state,
            result.confidence_level,
            json.dumps(result.matched_conditions),
            json.dumps(result.failed_conditions),
            json.dumps(result.missing_fields),
            json.dumps(result.exclusion_reasons),
            json.dumps(result.caveats),
            result.explanation,
            result.evaluated_at.isoformat(),
        ],
    )
    for exclusion in result.exclusions:
        conn.execute(
            """
            INSERT INTO screener_result_exclusions
                (run_id, symbol, reason_code, reason_detail, source_field)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                result.run_id,
                result.symbol,
                exclusion.reason_code,
                exclusion.reason_detail,
                exclusion.source_field,
            ],
        )


def _list_conditions(
    conn: duckdb.DuckDBPyConnection,
    rule_id: str,
) -> list[ScreenerCondition]:
    rows = conn.execute(
        """
        SELECT condition_id, field_name, operator, value_json, required_source_type,
               missing_behavior, description
        FROM screener_rule_conditions
        WHERE rule_id = ?
        ORDER BY condition_id
        """,
        [rule_id],
    ).fetchall()
    return [
        ScreenerCondition.model_validate(
            {
                "condition_id": str(row[0]),
                "field_name": str(row[1]),
                "operator": str(row[2]),
                "value": _optional_json(row[3]),
                "required_source_type": _optional_str(row[4]),
                "missing_behavior": str(row[5]),
                "description": _optional_str(row[6]),
            }
        )
        for row in rows
    ]


def _row_to_rule(row: tuple[object, ...], conditions: list[ScreenerCondition]) -> ScreenerRule:
    return ScreenerRule.model_validate(
        {
            "rule_id": str(row[0]),
            "name": str(row[1]),
            "description": str(row[2]),
            "required_fields": _json_list(row[3]),
            "required_source_types": _json_list(row[4]),
            "min_coverage_tier": str(row[5]),
            "allowed_freshness_states": _json_list(row[6]),
            "min_fundamental_completeness": _optional_str(row[7]),
            "min_confidence_level": _optional_str(row[8]),
            "is_active": bool(row[9]),
            "created_at": datetime.fromisoformat(str(row[10])),
            "updated_at": datetime.fromisoformat(str(row[11])),
            "conditions": conditions,
        }
    )


def _row_to_result(conn: duckdb.DuckDBPyConnection, row: tuple[object, ...]) -> ScreenerResult:
    exclusions = conn.execute(
        """
        SELECT reason_code, reason_detail, source_field
        FROM screener_result_exclusions
        WHERE run_id = ? AND symbol = ?
        ORDER BY reason_code, source_field
        """,
        [str(row[0]), str(row[1])],
    ).fetchall()
    return ScreenerResult.model_validate(
        {
            "run_id": str(row[0]),
            "symbol": str(row[1]),
            "result_status": str(row[2]),
            "coverage_tier": str(row[3]),
            "lifecycle_status": str(row[4]),
            "freshness_state": str(row[5]),
            "completeness_state": _optional_str(row[6]),
            "confidence_level": _optional_str(row[7]),
            "matched_conditions": _json_list(row[8]),
            "failed_conditions": _json_list(row[9]),
            "missing_fields": _json_list(row[10]),
            "exclusion_reasons": _json_list(row[11]),
            "caveats": _json_list(row[12]),
            "explanation": str(row[13]),
            "evaluated_at": datetime.fromisoformat(str(row[14])),
            "exclusions": [
                ScreenerExclusion(
                    reason_code=str(exclusion[0]),
                    reason_detail=str(exclusion[1]),
                    source_field=_optional_str(exclusion[2]),
                )
                for exclusion in exclusions
            ],
        }
    )


def _json_list(value: object) -> list[str]:
    parsed = json.loads(str(value))
    if not isinstance(parsed, list):
        raise ValueError("expected JSON list")
    return [str(item) for item in parsed]


def _optional_json(value: object) -> Any | None:
    return json.loads(str(value)) if value is not None else None


def _optional_str(value: object) -> str | None:
    return str(value) if value is not None else None
