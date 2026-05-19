"""Compute MVP indicators from DuckDB.price_history → DuckDB.indicator_cache.

Sources: explicit `--symbols A,B,C` or `--from-watchlist`.
Window: seluruh price history per symbol (full recompute, idempotent).
Output: human summary by default; `--json` for machine-consumable.
Exit code: 0 if all symbols ok; 2 if any partial; 3 if any/all failed.

Usage:
  uv run python -m scripts.calculate_indicators --from-watchlist
  uv run python -m scripts.calculate_indicators --symbols BBCA,TLKM --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import TypedDict

import duckdb
from packages.core.indicators import (
    compute_all,
    load_price_series,
    upsert_indicator_points,
)
from packages.core.schemas.repository import open_connection
from packages.core.watchlist import list_entries

EXIT_OK = 0
EXIT_PARTIAL = 2
EXIT_FAILED = 3


class SymbolResult(TypedDict):
    symbol: str
    points_written: int
    status: str  # "ok" | "empty" | "failed"
    error: str | None


class Summary(TypedDict):
    symbols_processed: list[str]
    points_written: int
    by_status: dict[str, list[str]]
    errors: dict[str, str]


def resolve_symbols(
    conn: duckdb.DuckDBPyConnection, *, explicit: list[str], from_watchlist: bool
) -> list[str]:
    if explicit:
        return explicit
    if from_watchlist:
        return [e.symbol for e in list_entries(conn)]
    return []


def compute_for_symbols(
    conn: duckdb.DuckDBPyConnection, symbols: Sequence[str]
) -> list[SymbolResult]:
    results: list[SymbolResult] = []
    for sym in symbols:
        try:
            prices = load_price_series(conn, sym)
            if prices.empty:
                results.append(
                    {"symbol": sym, "points_written": 0, "status": "empty", "error": None}
                )
                continue
            points = compute_all(sym, prices)
            written = upsert_indicator_points(conn, points)
            results.append(
                {"symbol": sym, "points_written": written, "status": "ok", "error": None}
            )
        except Exception as exc:
            results.append(
                {"symbol": sym, "points_written": 0, "status": "failed", "error": str(exc)}
            )
    return results


def summarize(results: Sequence[SymbolResult]) -> Summary:
    return {
        "symbols_processed": [r["symbol"] for r in results],
        "points_written": sum(r["points_written"] for r in results),
        "by_status": {
            "ok": [r["symbol"] for r in results if r["status"] == "ok"],
            "empty": [r["symbol"] for r in results if r["status"] == "empty"],
            "failed": [r["symbol"] for r in results if r["status"] == "failed"],
        },
        "errors": {r["symbol"]: r["error"] for r in results if r["error"]},
    }


def exit_code(results: Sequence[SymbolResult]) -> int:
    if not results:
        return EXIT_FAILED
    statuses = [r["status"] for r in results]
    if all(s == "failed" for s in statuses):
        return EXIT_FAILED
    if any(s in {"failed", "empty"} for s in statuses):
        return EXIT_PARTIAL
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute MVP indicators into DuckDB.indicator_cache."
    )
    parser.add_argument("--symbols", type=str, default="", help="Comma-separated tickers.")
    parser.add_argument("--from-watchlist", action="store_true", help="Use watchlist symbols.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")
    args = parser.parse_args(argv)

    explicit = [s for s in (args.symbols or "").split(",") if s.strip()]

    with open_connection(args.db) as conn:
        symbols = resolve_symbols(conn, explicit=explicit, from_watchlist=args.from_watchlist)
        if not symbols:
            print(
                "no symbols: pass --symbols or --from-watchlist (and ensure watchlist non-empty)",
                file=sys.stderr,
            )
            return EXIT_FAILED
        results = compute_for_symbols(conn, symbols)

    summary = summarize(results)
    if args.json:
        print(json.dumps(summary, default=str))
    else:
        print(f"points_written={summary['points_written']}")
        print(f"ok={summary['by_status']['ok']}")
        print(f"empty={summary['by_status']['empty']}")
        print(f"failed={summary['by_status']['failed']}")
        for sym, msg in summary["errors"].items():
            print(f"  {sym}: {msg}", file=sys.stderr)

    return exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
