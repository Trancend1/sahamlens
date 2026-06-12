"""V1-S4 weekly journal review and simple strategy-rule CLI."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, time
from typing import cast
from uuid import uuid4

import duckdb
from packages.core.journal.repo import list_plans
from packages.core.journal.review_repo import list_weekly_review_runs, upsert_weekly_review_run
from packages.core.journal.weekly_review import generate_weekly_journal_review
from packages.core.schemas.repository import open_connection
from packages.core.strategy import (
    StrategyRule,
    StrategyRuleEvaluation,
    default_strategy_rules,
    list_strategy_rule_evaluations,
    list_strategy_rules,
    upsert_strategy_rules,
)

EXIT_OK = 0


def cmd_review_generate(args: argparse.Namespace) -> int:
    period_start = _parse_start(args.start)
    period_end = _parse_end(args.end)
    generated_at = datetime.now(UTC)
    review_id = args.review_id or f"weekly-review-{uuid4().hex}"
    with open_connection(args.db) as conn:
        rules = _ensure_rules(conn, generated_at=generated_at)
        review = generate_weekly_journal_review(
            list_plans(conn),
            rules,
            review_id=review_id,
            period_start=period_start,
            period_end=period_end,
            generated_at=generated_at,
        )
        upsert_weekly_review_run(conn, review)
    _emit(review.model_dump(mode="json"), as_json=args.json)
    return EXIT_OK


def cmd_review_list(args: argparse.Namespace) -> int:
    with open_connection(args.db, read_only=True) as conn:
        reviews = list_weekly_review_runs(conn, limit=args.limit)
    _emit([review.model_dump(mode="json") for review in reviews], as_json=args.json)
    return EXIT_OK


def cmd_rules_list(args: argparse.Namespace) -> int:
    generated_at = datetime.now(UTC)
    with open_connection(args.db) as conn:
        _ensure_rules(conn, generated_at=generated_at)
        rules = list_strategy_rules(conn, active_only=args.active_only)
    _emit([rule.model_dump(mode="json") for rule in rules], as_json=args.json)
    return EXIT_OK


def cmd_rules_evaluate(args: argparse.Namespace) -> int:
    period_start = _parse_start(args.start)
    period_end = _parse_end(args.end)
    generated_at = datetime.now(UTC)
    review_id = args.review_id or f"strategy-eval-{uuid4().hex}"
    with open_connection(args.db) as conn:
        rules = _ensure_rules(conn, generated_at=generated_at)
        review = generate_weekly_journal_review(
            list_plans(conn),
            rules,
            review_id=review_id,
            period_start=period_start,
            period_end=period_end,
            generated_at=generated_at,
        )
        upsert_weekly_review_run(conn, review)
    payload = {
        "review_id": review.review_id,
        "evaluation_count": review.rule_evaluation_count,
        "violation_count": review.violation_count,
        "needs_data_count": review.needs_data_count,
        "evaluations": [
            item.model_dump(mode="json")
            for item in cast(list[StrategyRuleEvaluation], review.rule_evaluations)
        ],
    }
    _emit(payload, as_json=args.json)
    return EXIT_OK


def cmd_rules_results(args: argparse.Namespace) -> int:
    with open_connection(args.db, read_only=True) as conn:
        evaluations = list_strategy_rule_evaluations(conn, review_id=args.review_id)
    _emit([evaluation.model_dump(mode="json") for evaluation in evaluations], as_json=args.json)
    return EXIT_OK


def _ensure_rules(
    conn: duckdb.DuckDBPyConnection,
    *,
    generated_at: datetime,
) -> list[StrategyRule]:
    existing = list_strategy_rules(conn, active_only=True)
    if existing:
        return existing
    rules = default_strategy_rules(now=generated_at)
    upsert_strategy_rules(conn, rules)
    return rules


def _parse_start(value: str) -> datetime:
    return datetime.combine(datetime.fromisoformat(value).date(), time.min, tzinfo=UTC)


def _parse_end(value: str) -> datetime:
    return datetime.combine(datetime.fromisoformat(value).date(), time.max, tzinfo=UTC)


def _emit(payload: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload))
        return
    print(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SahamLens weekly journal review CLI.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")

    sub = parser.add_subparsers(dest="domain", required=True)

    review_p = sub.add_parser("review", help="Weekly journal review commands.")
    review_sub = review_p.add_subparsers(dest="cmd", required=True)

    p_review_generate = review_sub.add_parser("generate", help="Generate weekly review.")
    p_review_generate.add_argument("--start", required=True)
    p_review_generate.add_argument("--end", required=True)
    p_review_generate.add_argument("--review-id", default=None)
    p_review_generate.set_defaults(func=cmd_review_generate)

    p_review_list = review_sub.add_parser("list", help="List weekly reviews.")
    p_review_list.add_argument("--limit", type=int, default=20)
    p_review_list.set_defaults(func=cmd_review_list)

    rules_p = sub.add_parser("rules", help="Simple strategy-rule commands.")
    rules_sub = rules_p.add_subparsers(dest="cmd", required=True)

    p_rules_list = rules_sub.add_parser("list", help="List simple named rules.")
    p_rules_list.add_argument("--active-only", action="store_true")
    p_rules_list.set_defaults(func=cmd_rules_list)

    p_rules_evaluate = rules_sub.add_parser("evaluate", help="Evaluate rules for date range.")
    p_rules_evaluate.add_argument("--start", required=True)
    p_rules_evaluate.add_argument("--end", required=True)
    p_rules_evaluate.add_argument("--review-id", default=None)
    p_rules_evaluate.set_defaults(func=cmd_rules_evaluate)

    p_rules_results = rules_sub.add_parser("results", help="List persisted rule evaluations.")
    p_rules_results.add_argument("--review-id", default=None)
    p_rules_results.set_defaults(func=cmd_rules_results)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
