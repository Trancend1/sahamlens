"""Transparent screener CLI for V1-S3.

Examples:
  uv run python -m scripts.screener --json run --builtin fundamentals-basic --from-watchlist
  uv run python -m scripts.screener --json run --rule-id fundamentals-basic --symbols BBCA,TLKM
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import duckdb
from packages.core.fundamentals import get_latest_fundamental_snapshot
from packages.core.schemas.repository import load_ohlcv, open_connection
from packages.core.screener import (
    ScreenerCandidate,
    ScreenerCondition,
    ScreenerRule,
    evaluate_screener_rule,
    get_screener_rule,
    upsert_screener_run,
)
from packages.core.ticker_coverage import (
    get_ticker_lifecycle_snapshot,
    list_source_coverage_snapshots,
)
from packages.core.watchlist import list_entries

EXIT_OK = 0
EXIT_FAILED = 3


def cmd_run(args: argparse.Namespace) -> int:
    with open_connection(args.db, read_only=args.no_persist) as conn:
        rule = _resolve_rule(conn, builtin=args.builtin, rule_id=args.rule_id)
        if rule is None:
            print("screener rule not found", file=sys.stderr)
            return EXIT_FAILED
        symbols = _resolve_symbols(
            conn,
            explicit=_parse_csv(args.symbols),
            from_watchlist=args.from_watchlist,
        )
        if not symbols:
            print(
                "no symbols: pass --symbols or --from-watchlist (and ensure watchlist non-empty)",
                file=sys.stderr,
            )
            return EXIT_FAILED
        run = evaluate_screener_rule(
            rule,
            _load_candidates(conn, symbols),
            run_id=args.run_id or f"screener-{uuid4().hex}",
            evaluated_at=datetime.now(UTC),
        )
        if not args.no_persist:
            upsert_screener_run(conn, run)

    _emit(run.model_dump(mode="json"), as_json=args.json)
    return EXIT_OK


def _resolve_rule(
    conn: duckdb.DuckDBPyConnection,
    *,
    builtin: str | None,
    rule_id: str | None,
) -> ScreenerRule | None:
    if rule_id:
        return get_screener_rule(conn, rule_id)
    if builtin == "fundamentals-basic":
        return fundamentals_basic_rule()
    return None


def fundamentals_basic_rule(*, now: datetime | None = None) -> ScreenerRule:
    timestamp = now or datetime.now(UTC)
    return ScreenerRule(
        rule_id="fundamentals-basic",
        name="Fundamental completeness filter",
        description="Filters symbols with visible coverage and fundamental fields.",
        required_fields=["market_cap", "roe"],
        required_source_types=["ohlcv", "fundamental"],
        min_coverage_tier="tier_b",
        allowed_freshness_states=["fresh", "delayed"],
        min_fundamental_completeness="partial",
        min_confidence_level="medium",
        conditions=[
            ScreenerCondition(
                condition_id="fundamentals-basic-market-cap-exists",
                field_name="market_cap",
                operator="exists",
                missing_behavior="exclude",
            ),
            ScreenerCondition(
                condition_id="fundamentals-basic-roe-exists",
                field_name="roe",
                operator="exists",
                missing_behavior="exclude",
            ),
        ],
        created_at=timestamp,
        updated_at=timestamp,
    )


def _load_candidates(
    conn: duckdb.DuckDBPyConnection,
    symbols: Sequence[str],
) -> list[ScreenerCandidate]:
    candidates: list[ScreenerCandidate] = []
    for symbol in symbols:
        candidates.append(
            ScreenerCandidate(
                symbol=symbol,
                coverage=get_ticker_lifecycle_snapshot(conn, symbol),
                source_coverage=list_source_coverage_snapshots(conn, symbol=symbol),
                fundamental=get_latest_fundamental_snapshot(conn, symbol),
                price_fields=_latest_price_fields(conn, symbol),
            )
        )
    return candidates


def _latest_price_fields(conn: duckdb.DuckDBPyConnection, symbol: str) -> dict[str, Any]:
    rows = load_ohlcv(conn, symbol, limit=1)
    if not rows:
        return {}
    latest = rows[-1]
    return {
        "close": latest["close"],
        "volume": latest["volume"],
    }


def _resolve_symbols(
    conn: duckdb.DuckDBPyConnection,
    *,
    explicit: list[str],
    from_watchlist: bool,
) -> list[str]:
    from packages.core.data_sources.normalize import normalize_ticker

    if explicit:
        return [normalize_ticker(symbol) for symbol in explicit]
    if from_watchlist:
        return [entry.symbol for entry in list_entries(conn)]
    return []


def _parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def _emit(payload: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload))
        return
    print(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SahamLens transparent screener CLI.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run a saved or built-in screener rule.")
    p_run.add_argument("--builtin", default="fundamentals-basic")
    p_run.add_argument("--rule-id", default=None)
    p_run.add_argument("--symbols", default="")
    p_run.add_argument("--from-watchlist", action="store_true")
    p_run.add_argument("--run-id", default=None)
    p_run.add_argument("--no-persist", action="store_true")
    p_run.set_defaults(func=cmd_run)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
