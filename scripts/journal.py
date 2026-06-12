"""Trade journal CLI: plan add / list / get / critique.

Examples:
  uv run python -m scripts.journal plan add --json '{"symbol":"BBCA","setup_type":"breakout",...}'
  uv run python -m scripts.journal plan list
  uv run python -m scripts.journal plan list --symbol BBCA --status planned
  uv run python -m scripts.journal plan get --id 1234567890
  uv run python -m scripts.journal plan critique --id 1234567890
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from datetime import UTC, datetime

from packages.core.ai.critique_plan import critique_trade_plan
from packages.core.ai.provider import AnthropicProvider
from packages.core.ai.router import CircuitBreaker, ModelRouter, load_budget
from packages.core.journal.models import TradePlan
from packages.core.journal.repo import create_plan, list_plans, load_plan, update_status
from packages.core.schemas.repository import open_connection


def cmd_plan_add(args: argparse.Namespace) -> int:
    raw = json.loads(args.json_data)
    if "id" not in raw:
        raw["id"] = int(time.time() * 1_000_000)
    if "created_at" not in raw:
        raw["created_at"] = datetime.now(UTC).isoformat()
    plan = TradePlan.model_validate(raw)
    with open_connection(args.db) as conn:
        create_plan(conn, plan)
    print(json.dumps(plan.model_dump(mode="json")))
    return 0


def cmd_plan_list(args: argparse.Namespace) -> int:
    with open_connection(args.db, read_only=True) as conn:
        plans = list_plans(
            conn,
            symbol=args.symbol or None,
            status=args.status or None,
        )
    print(json.dumps([p.model_dump(mode="json") for p in plans]))
    return 0


def cmd_plan_get(args: argparse.Namespace) -> int:
    with open_connection(args.db, read_only=True) as conn:
        plan = load_plan(conn, args.id)
    if plan is None:
        print(f"plan {args.id} not found", file=sys.stderr)
        return 2
    print(json.dumps(plan.model_dump(mode="json")))
    return 0


def cmd_plan_update(args: argparse.Namespace) -> int:
    with open_connection(args.db) as conn:
        plan = load_plan(conn, args.id)
        if plan is None:
            print(f"plan {args.id} not found", file=sys.stderr)
            return 2
        update_status(
            conn,
            args.id,
            args.status,
            result_rupiah=args.result_rupiah,
            lesson=args.lesson,
        )
        updated = load_plan(conn, args.id)
    print(json.dumps(updated.model_dump(mode="json") if updated else {}))
    return 0


def cmd_plan_critique(args: argparse.Namespace) -> int:
    with open_connection(args.db) as conn:
        plan = load_plan(conn, args.id)
        if plan is None:
            print(f"plan {args.id} not found", file=sys.stderr)
            return 2
        provider = AnthropicProvider()
        router = ModelRouter()
        breaker = CircuitBreaker(load_budget())
        critique = critique_trade_plan(
            plan,
            provider=provider,
            router=router,
            breaker=breaker,
            conn=conn,
        )
    if critique is None:
        print(json.dumps({"error": "critique unavailable"}))
        return 3
    print(json.dumps(critique.model_dump(mode="json")))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SahamLens journal CLI.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")

    sub = parser.add_subparsers(dest="domain", required=True)

    plan_p = sub.add_parser("plan", help="Trade plan commands.")
    plan_sub = plan_p.add_subparsers(dest="cmd", required=True)

    p_add = plan_sub.add_parser("add", help="Add a trade plan (JSON input).")
    p_add.add_argument("--json", dest="json_data", required=True, help="Plan JSON string.")
    p_add.set_defaults(func=cmd_plan_add)

    p_list = plan_sub.add_parser("list", help="List trade plans.")
    p_list.add_argument("--symbol", default=None)
    p_list.add_argument("--status", default=None)
    p_list.set_defaults(func=cmd_plan_list)

    p_get = plan_sub.add_parser("get", help="Get a single plan by id.")
    p_get.add_argument("--id", type=int, required=True)
    p_get.set_defaults(func=cmd_plan_get)

    p_update = plan_sub.add_parser("update", help="Update plan status.")
    p_update.add_argument("--id", type=int, required=True)
    p_update.add_argument(
        "--status", required=True, choices=["planned", "open", "closed", "skipped"]
    )
    p_update.add_argument("--result-rupiah", type=int, default=None)
    p_update.add_argument("--lesson", default=None)
    p_update.set_defaults(func=cmd_plan_update)

    p_critique = plan_sub.add_parser("critique", help="Generate AI critique for a plan.")
    p_critique.add_argument("--id", type=int, required=True)
    p_critique.set_defaults(func=cmd_plan_critique)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
