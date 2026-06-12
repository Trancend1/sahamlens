"""Ingest EOD OHLCV from yfinance into DuckDB.price_history.

Sources: explicit `--symbols A,B,C` or `--from-watchlist`.
Window: last `--days N` (default 60), ending today (UTC).
Output: human summary by default; `--json` for machine-consumable.
Exit code: 0 if all symbols ok; 2 if any partial; 3 if any failed.

Usage:
  uv run python -m scripts.ingest_prices --from-watchlist --days 30
  uv run python -m scripts.ingest_prices --symbols BBCA,TLKM --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from typing import TypedDict

import duckdb
from packages.core.data_sources.base import PriceSource
from packages.core.data_sources.yfinance import YFinanceSource
from packages.core.schemas.models import FetchResult
from packages.core.schemas.repository import open_connection, upsert_price_rows
from packages.core.watchlist import list_entries

EXIT_OK = 0
EXIT_PARTIAL = 2
EXIT_FAILED = 3


def resolve_symbols(
    conn: duckdb.DuckDBPyConnection, *, explicit: list[str], from_watchlist: bool
) -> list[str]:
    if explicit:
        return explicit
    if from_watchlist:
        return [e.symbol for e in list_entries(conn)]
    return []


def ingest(
    conn: duckdb.DuckDBPyConnection,
    source: PriceSource,
    symbols: Sequence[str],
    *,
    start: date,
    end: date,
) -> list[FetchResult]:
    results: list[FetchResult] = []
    for sym in symbols:
        result = source.fetch_ohlcv(sym, start, end)
        if result.status != "failed":
            upsert_price_rows(conn, result.rows)
        results.append(result)
    return results


def fetch_ohlcv_results(
    source: PriceSource,
    symbols: Sequence[str],
    *,
    start: date,
    end: date,
) -> list[FetchResult]:
    return [source.fetch_ohlcv(sym, start, end) for sym in symbols]


class Summary(TypedDict):
    rows_written: int
    by_status: dict[str, list[str]]
    errors: dict[str, str]


def summarize(results: Sequence[FetchResult]) -> Summary:
    return {
        "rows_written": sum(len(r.rows) for r in results),
        "by_status": {
            "ok": [r.symbol for r in results if r.status == "ok"],
            "partial": [r.symbol for r in results if r.status == "partial"],
            "failed": [r.symbol for r in results if r.status == "failed"],
        },
        "errors": {r.symbol: r.error_message for r in results if r.error_message},
    }


def exit_code(results: Sequence[FetchResult]) -> int:
    if any(r.status == "failed" for r in results):
        return EXIT_FAILED
    if any(r.status == "partial" for r in results):
        return EXIT_PARTIAL
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest OHLCV from yfinance into DuckDB.")
    parser.add_argument("--symbols", type=str, default="", help="Comma-separated tickers.")
    parser.add_argument("--from-watchlist", action="store_true", help="Use watchlist symbols.")
    parser.add_argument("--days", type=int, default=60, help="Window size in days (default 60).")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")
    args = parser.parse_args(argv)

    explicit = [s for s in (args.symbols or "").split(",") if s.strip()]

    with open_connection(args.db, read_only=True) as conn:
        symbols = resolve_symbols(conn, explicit=explicit, from_watchlist=args.from_watchlist)
    if not symbols:
        print(
            "no symbols: pass --symbols or --from-watchlist (and ensure watchlist non-empty)",
            file=sys.stderr,
        )
        return EXIT_FAILED

    end = datetime.now(UTC).date()
    start = end - timedelta(days=args.days)
    source = YFinanceSource()
    results = fetch_ohlcv_results(source, symbols, start=start, end=end)
    with open_connection(args.db) as conn:
        for result in results:
            if result.status != "failed":
                upsert_price_rows(conn, result.rows)

    summary = summarize(results)
    if args.json:
        print(json.dumps(summary, default=str))
    else:
        print(f"rows_written={summary['rows_written']}")
        print(f"ok={summary['by_status']['ok']}")
        print(f"partial={summary['by_status']['partial']}")
        print(f"failed={summary['by_status']['failed']}")
        for sym, msg in summary["errors"].items():
            print(f"  {sym}: {msg}", file=sys.stderr)

    return exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
