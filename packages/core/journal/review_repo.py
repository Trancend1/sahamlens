"""DuckDB persistence for weekly journal review runs and findings."""

from __future__ import annotations

import json
from datetime import datetime
from typing import cast

import duckdb
from packages.core.journal.models import WeeklyReviewFinding, WeeklyReviewRun
from packages.core.strategy.models import StrategyRuleEvaluation
from packages.core.strategy.repo import (
    list_strategy_rule_evaluations,
    upsert_strategy_rule_evaluations,
)


def upsert_weekly_review_run(conn: duckdb.DuckDBPyConnection, review: WeeklyReviewRun) -> int:
    conn.execute(
        """
        INSERT INTO weekly_review_runs
            (review_id, period_start, period_end, generated_at, status,
             journal_entry_count, reviewed_plan_count, rule_evaluation_count,
             violation_count, needs_data_count, summary, evidence, caveats, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (review_id) DO UPDATE SET
            period_start = EXCLUDED.period_start,
            period_end = EXCLUDED.period_end,
            generated_at = EXCLUDED.generated_at,
            status = EXCLUDED.status,
            journal_entry_count = EXCLUDED.journal_entry_count,
            reviewed_plan_count = EXCLUDED.reviewed_plan_count,
            rule_evaluation_count = EXCLUDED.rule_evaluation_count,
            violation_count = EXCLUDED.violation_count,
            needs_data_count = EXCLUDED.needs_data_count,
            summary = EXCLUDED.summary,
            evidence = EXCLUDED.evidence,
            caveats = EXCLUDED.caveats
        """,
        [
            review.review_id,
            review.period_start.isoformat(),
            review.period_end.isoformat(),
            review.generated_at.isoformat(),
            review.status,
            review.journal_entry_count,
            review.reviewed_plan_count,
            review.rule_evaluation_count,
            review.violation_count,
            review.needs_data_count,
            review.summary,
            json.dumps(review.evidence),
            json.dumps(review.caveats),
            review.generated_at.isoformat(),
        ],
    )
    conn.execute("DELETE FROM weekly_review_findings WHERE review_id = ?", [review.review_id])
    for finding in review.findings:
        _insert_finding(conn, finding)
    upsert_strategy_rule_evaluations(
        conn, cast(list[StrategyRuleEvaluation], review.rule_evaluations)
    )
    return 1


def list_weekly_review_runs(
    conn: duckdb.DuckDBPyConnection,
    *,
    limit: int = 20,
) -> list[WeeklyReviewRun]:
    rows = conn.execute(
        """
        SELECT review_id, period_start, period_end, generated_at, status,
               journal_entry_count, reviewed_plan_count, rule_evaluation_count,
               violation_count, needs_data_count, summary, evidence, caveats, created_at
        FROM weekly_review_runs
        ORDER BY generated_at DESC
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    return [_row_to_review(conn, row) for row in rows]


def get_weekly_review_run(
    conn: duckdb.DuckDBPyConnection,
    review_id: str,
) -> WeeklyReviewRun | None:
    row = conn.execute(
        """
        SELECT review_id, period_start, period_end, generated_at, status,
               journal_entry_count, reviewed_plan_count, rule_evaluation_count,
               violation_count, needs_data_count, summary, evidence, caveats, created_at
        FROM weekly_review_runs
        WHERE review_id = ?
        """,
        [review_id],
    ).fetchone()
    if row is None:
        return None
    return _row_to_review(conn, row)


def _insert_finding(
    conn: duckdb.DuckDBPyConnection,
    finding: WeeklyReviewFinding,
) -> None:
    conn.execute(
        """
        INSERT INTO weekly_review_findings
            (finding_id, review_id, finding_type, title, detail, severity,
             evidence, caveats, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            finding.finding_id,
            finding.review_id,
            finding.finding_type,
            finding.title,
            finding.detail,
            finding.severity,
            json.dumps(finding.evidence),
            json.dumps(finding.caveats),
            finding.created_at.isoformat(),
        ],
    )


def _row_to_review(conn: duckdb.DuckDBPyConnection, row: tuple[object, ...]) -> WeeklyReviewRun:
    review_id = str(row[0])
    return WeeklyReviewRun.model_validate(
        {
            "review_id": review_id,
            "period_start": datetime.fromisoformat(str(row[1])),
            "period_end": datetime.fromisoformat(str(row[2])),
            "generated_at": datetime.fromisoformat(str(row[3])),
            "status": str(row[4]),
            "journal_entry_count": int(row[5]),
            "reviewed_plan_count": int(row[6]),
            "rule_evaluation_count": int(row[7]),
            "violation_count": int(row[8]),
            "needs_data_count": int(row[9]),
            "summary": str(row[10]),
            "evidence": _json_list(row[11]),
            "caveats": _json_list(row[12]),
            "findings": _list_findings(conn, review_id),
            "rule_evaluations": list_strategy_rule_evaluations(conn, review_id=review_id),
        }
    )


def _list_findings(
    conn: duckdb.DuckDBPyConnection,
    review_id: str,
) -> list[WeeklyReviewFinding]:
    rows = conn.execute(
        """
        SELECT finding_id, review_id, finding_type, title, detail, severity,
               evidence, caveats, created_at
        FROM weekly_review_findings
        WHERE review_id = ?
        ORDER BY created_at, finding_id
        """,
        [review_id],
    ).fetchall()
    return [
        WeeklyReviewFinding.model_validate(
            {
                "finding_id": str(row[0]),
                "review_id": str(row[1]),
                "finding_type": str(row[2]),
                "title": str(row[3]),
                "detail": str(row[4]),
                "severity": str(row[5]),
                "evidence": _json_list(row[6]),
                "caveats": _json_list(row[7]),
                "created_at": datetime.fromisoformat(str(row[8])),
            }
        )
        for row in rows
    ]


def _json_list(value: object) -> list[str]:
    parsed = json.loads(str(value))
    if not isinstance(parsed, list):
        raise ValueError("expected JSON list")
    return [str(item) for item in parsed]
