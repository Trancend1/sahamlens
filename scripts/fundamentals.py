"""Ticker coverage and fundamental snapshot CLI for V1-S2.

Examples:
  uv run python -m scripts.fundamentals --json ingest --symbol BBCA --period 2026Q1 --field roe=0.18
  uv run python -m scripts.fundamentals --json refresh-coverage --from-watchlist --lifecycle-status active
  uv run python -m scripts.fundamentals --json snapshot --symbol BBCA
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast

import duckdb
from packages.core.data_quality.models import FreshnessState, ProviderTrustTier
from packages.core.data_quality.repo import list_provider_health_snapshots
from packages.core.fundamentals import (
    build_fundamental_snapshot,
    get_latest_fundamental_snapshot,
    list_fundamental_snapshots,
    upsert_fundamental_snapshot,
)
from packages.core.schemas.repository import open_connection
from packages.core.ticker_coverage import (
    SourceCoverageSnapshot,
    classify_ticker_coverage,
    get_ticker_lifecycle_snapshot,
    list_source_coverage_snapshots,
    list_ticker_lifecycle_snapshots,
    upsert_source_coverage_snapshot,
    upsert_ticker_lifecycle_snapshot,
)
from packages.core.ticker_coverage.models import LifecycleStatus
from packages.core.watchlist import list_entries

EXIT_OK = 0
EXIT_FAILED = 3
DEFAULT_REQUIRED_FIELDS = ["market_cap", "pe_ratio", "pbv", "roe"]


def cmd_ingest(args: argparse.Namespace) -> int:
    now = datetime.now(UTC)
    fields = _parse_fields(args.field)
    required_fields = _parse_csv(args.required_fields) or DEFAULT_REQUIRED_FIELDS
    with open_connection(args.db) as conn:
        symbols = _resolve_symbols(
            conn, explicit=[args.symbol] if args.symbol else [], from_watchlist=False
        )
        if not symbols:
            print("no symbol: pass --symbol", file=sys.stderr)
            return EXIT_FAILED
        snapshot = build_fundamental_snapshot(
            symbol=symbols[0],
            period=args.period,
            source=args.source,
            source_type=args.source_type,
            data_fields=fields,
            required_fields=required_fields,
            coverage_tier=args.coverage_tier,
            freshness_state=args.freshness_state,
            provider_trust_tier=args.provider_trust_tier,
            fetched_at=now,
            imported_at=now,
        )
        upsert_fundamental_snapshot(conn, snapshot)
    _emit(snapshot.model_dump(mode="json"), as_json=args.json)
    return EXIT_OK


def cmd_list(args: argparse.Namespace) -> int:
    with open_connection(args.db) as conn:
        snapshots = [
            snapshot.model_dump(mode="json")
            for snapshot in list_fundamental_snapshots(conn, symbol=args.symbol)
        ]
    _emit(snapshots, as_json=args.json)
    return EXIT_OK


def cmd_refresh_coverage(args: argparse.Namespace) -> int:
    with open_connection(args.db) as conn:
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
        snapshots = refresh_ticker_coverage(
            conn,
            symbols,
            lifecycle_status=args.lifecycle_status,
            checked_at=datetime.now(UTC),
        )
    _emit([snapshot.model_dump(mode="json") for snapshot in snapshots], as_json=args.json)
    return EXIT_OK


def cmd_coverage_list(args: argparse.Namespace) -> int:
    with open_connection(args.db) as conn:
        snapshots = [
            snapshot.model_dump(mode="json") for snapshot in list_ticker_lifecycle_snapshots(conn)
        ]
    _emit(snapshots, as_json=args.json)
    return EXIT_OK


def cmd_snapshot(args: argparse.Namespace) -> int:
    with open_connection(args.db) as conn:
        symbol = _resolve_symbols(conn, explicit=[args.symbol], from_watchlist=False)[0]
        coverage = get_ticker_lifecycle_snapshot(conn, symbol)
        fundamental = get_latest_fundamental_snapshot(conn, symbol)
        sources = list_source_coverage_snapshots(conn, symbol=symbol)
    payload = {
        "symbol": symbol,
        "coverage": coverage.model_dump(mode="json") if coverage else None,
        "fundamental": fundamental.model_dump(mode="json") if fundamental else None,
        "source_coverage": [source.model_dump(mode="json") for source in sources],
    }
    _emit(payload, as_json=args.json)
    return EXIT_OK


def refresh_ticker_coverage(
    conn: duckdb.DuckDBPyConnection,
    symbols: Sequence[str],
    *,
    lifecycle_status: LifecycleStatus,
    checked_at: datetime,
) -> list[Any]:
    provider_health = _ohlcv_provider_health(conn)
    snapshots = []
    for symbol in symbols:
        price_info = _latest_price_fetch(conn, symbol)
        freshness_state = cast(
            FreshnessState,
            provider_health["freshness_state"] if provider_health else "unknown",
        )
        provider_trust_tier = cast(
            ProviderTrustTier,
            provider_health["provider_trust_tier"] if provider_health else "tier_3",
        )
        source_coverage = SourceCoverageSnapshot(
            symbol=symbol,
            provider_name="yfinance",
            source_type="ohlcv",
            provider_trust_tier=provider_trust_tier,
            availability_state="available" if price_info else "missing",
            freshness_state=freshness_state if price_info else "unknown",
            last_success_at=price_info,
            last_checked_at=checked_at,
            missing_reason=None if price_info else "no local price_history rows",
            coverage_count=1 if price_info else 0,
        )
        upsert_source_coverage_snapshot(conn, source_coverage)
        fundamental = get_latest_fundamental_snapshot(conn, symbol)
        lifecycle = classify_ticker_coverage(
            symbol=symbol,
            lifecycle_status=lifecycle_status,
            ohlcv_available=price_info is not None,
            ohlcv_freshness_state=source_coverage.freshness_state,
            provider_health_visible=provider_health is not None,
            fundamental_completeness=fundamental.completeness_state if fundamental else None,
            source="manual",
            checked_at=checked_at,
        )
        upsert_ticker_lifecycle_snapshot(conn, lifecycle)
        snapshots.append(lifecycle)
    return snapshots


def _ohlcv_provider_health(conn: duckdb.DuckDBPyConnection) -> dict[str, str] | None:
    for provider in list_provider_health_snapshots(conn):
        if provider.provider_name == "yfinance" and provider.source_type == "ohlcv":
            return {
                "freshness_state": provider.freshness_state,
                "provider_trust_tier": provider.provider_trust_tier,
            }
    return None


def _latest_price_fetch(conn: duckdb.DuckDBPyConnection, symbol: str) -> datetime | None:
    row = conn.execute(
        "SELECT MAX(fetched_at) FROM price_history WHERE symbol = ?",
        [_resolve_symbols(conn, explicit=[symbol], from_watchlist=False)[0]],
    ).fetchone()
    return datetime.fromisoformat(str(row[0])) if row and row[0] else None


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


def _parse_fields(raw_fields: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for raw in raw_fields:
        if "=" not in raw:
            raise ValueError(f"field must use key=value: {raw}")
        key, value = raw.split("=", 1)
        parsed[key.strip()] = _coerce_value(value.strip())
    return parsed


def _coerce_value(value: str) -> Any:
    if value == "":
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _emit(payload: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload))
        return
    print(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SahamLens fundamentals and coverage CLI.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest", help="Ingest one lightweight fundamental snapshot.")
    p_ingest.add_argument("--symbol", required=True)
    p_ingest.add_argument("--period", required=True)
    p_ingest.add_argument("--source", default="manual")
    p_ingest.add_argument(
        "--source-type",
        default="manual",
        choices=["manual", "official", "public_provider", "other"],
    )
    p_ingest.add_argument("--field", action="append", default=[])
    p_ingest.add_argument("--required-fields", default=",".join(DEFAULT_REQUIRED_FIELDS))
    p_ingest.add_argument(
        "--coverage-tier", default="tier_b", choices=["tier_a", "tier_b", "tier_c"]
    )
    p_ingest.add_argument(
        "--freshness-state",
        default="delayed",
        choices=["fresh", "delayed", "stale", "failed", "partial", "unknown"],
    )
    p_ingest.add_argument(
        "--provider-trust-tier", default="tier_3", choices=["tier_1", "tier_2", "tier_3", "tier_4"]
    )
    p_ingest.set_defaults(func=cmd_ingest)

    p_list = sub.add_parser("list", help="List fundamental snapshots.")
    p_list.add_argument("--symbol", default=None)
    p_list.set_defaults(func=cmd_list)

    p_refresh = sub.add_parser(
        "refresh-coverage", help="Refresh ticker lifecycle/coverage from local data."
    )
    p_refresh.add_argument("--symbols", default="")
    p_refresh.add_argument("--from-watchlist", action="store_true")
    p_refresh.add_argument(
        "--lifecycle-status",
        default="unknown",
        choices=["active", "suspended", "delisted", "renamed", "unknown"],
    )
    p_refresh.set_defaults(func=cmd_refresh_coverage)

    p_coverage = sub.add_parser("coverage-list", help="List ticker lifecycle/coverage snapshots.")
    p_coverage.set_defaults(func=cmd_coverage_list)

    p_snapshot = sub.add_parser("snapshot", help="Show combined coverage/fundamental snapshot.")
    p_snapshot.add_argument("--symbol", required=True)
    p_snapshot.set_defaults(func=cmd_snapshot)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
