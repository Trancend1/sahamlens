"""Provider health CLI for V1 Data Quality foundation.

Examples:
  uv run python -m scripts.provider_health --json list
  uv run python -m scripts.provider_health --json refresh-yfinance --symbols BBCA,TLKM
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta

import duckdb
from packages.core.data_quality.models import (
    DataQualityOverview,
    FreshnessState,
    ProviderHealthSnapshot,
)
from packages.core.data_quality.repo import (
    load_data_quality_overview,
    upsert_provider_health_snapshot,
)
from packages.core.data_sources.base import PriceSource
from packages.core.data_sources.yfinance import YFinanceSource
from packages.core.schemas.models import FetchResult
from packages.core.schemas.repository import open_connection
from packages.core.watchlist import list_entries

EXIT_OK = 0
EXIT_FAILED = 3


def resolve_symbols(
    conn: duckdb.DuckDBPyConnection, *, explicit: list[str], from_watchlist: bool
) -> list[str]:
    if explicit:
        return explicit
    if from_watchlist:
        return [entry.symbol for entry in list_entries(conn)]
    return []


def refresh_yfinance_provider_health(
    conn: duckdb.DuckDBPyConnection,
    source: PriceSource,
    symbols: Sequence[str],
    *,
    start: date,
    end: date,
    updated_at: datetime | None = None,
) -> ProviderHealthSnapshot:
    results = [source.fetch_ohlcv(symbol, start, end) for symbol in symbols]
    snapshot = build_yfinance_snapshot(
        source_name=source.name,
        results=results,
        updated_at=updated_at or datetime.now(UTC),
    )
    upsert_provider_health_snapshot(conn, snapshot)
    return snapshot


def build_yfinance_snapshot(
    *,
    source_name: str,
    results: Sequence[FetchResult],
    updated_at: datetime,
) -> ProviderHealthSnapshot:
    if not results:
        return ProviderHealthSnapshot(
            provider_name=source_name,
            provider_trust_tier="tier_3",
            source_type="ohlcv",
            freshness_state="unknown",
            updated_at=updated_at,
            coverage_count=0,
        )

    successes = [result for result in results if result.status == "ok"]
    partials = [result for result in results if result.status == "partial"]
    failures = [result for result in results if result.status == "failed"]

    if successes and not partials and not failures:
        freshness_state: FreshnessState = "fresh"
    elif failures and not successes and not partials:
        freshness_state = "failed"
    else:
        freshness_state = "partial"

    successful_results = [*successes, *partials]
    last_success_at = max((result.fetched_at for result in successful_results), default=None)
    last_failure_at = max((result.fetched_at for result in failures), default=None)

    return ProviderHealthSnapshot(
        provider_name=source_name,
        provider_trust_tier="tier_3",
        source_type="ohlcv",
        freshness_state=freshness_state,
        updated_at=updated_at,
        last_success_at=last_success_at,
        last_failure_at=last_failure_at,
        last_failure_reason=_failure_reason(failures),
        consecutive_failure_count=len(failures),
        coverage_count=len(successes),
    )


def _failure_reason(failures: Sequence[FetchResult]) -> str | None:
    if not failures:
        return None
    return "; ".join(
        f"{result.symbol}: {result.error_message or 'fetch failed'}" for result in failures
    )


def cmd_list(args: argparse.Namespace) -> int:
    with open_connection(args.db) as conn:
        overview = load_data_quality_overview(conn)
    _emit_overview(overview_payload(overview), as_json=args.json)
    return EXIT_OK


def cmd_refresh_yfinance(args: argparse.Namespace) -> int:
    explicit = [symbol for symbol in (args.symbols or "").split(",") if symbol.strip()]
    with open_connection(args.db) as conn:
        symbols = resolve_symbols(conn, explicit=explicit, from_watchlist=args.from_watchlist)
        if not symbols:
            print(
                "no symbols: pass --symbols or --from-watchlist (and ensure watchlist non-empty)",
                file=sys.stderr,
            )
            return EXIT_FAILED
        end = datetime.now(UTC).date()
        start = end - timedelta(days=args.days)
        refresh_yfinance_provider_health(
            conn,
            YFinanceSource(),
            symbols,
            start=start,
            end=end,
        )
        overview = load_data_quality_overview(conn)
    _emit_overview(overview_payload(overview), as_json=args.json)
    return EXIT_OK


def overview_payload(overview: DataQualityOverview) -> dict[str, object]:
    return {
        "providers": [_provider_payload(provider) for provider in overview.providers],
        "provider_count": overview.provider_count,
        "failed_provider_count": overview.failed_provider_count,
        "stale_provider_count": overview.stale_provider_count,
        "restricted_provider_count": overview.restricted_provider_count,
        "total_coverage_count": overview.total_coverage_count,
    }


def _provider_payload(provider: ProviderHealthSnapshot) -> dict[str, object]:
    payload = provider.model_dump(mode="json")
    payload["supports_dependent_flows"] = provider.supports_dependent_flows
    payload["requires_caveat"] = provider.requires_caveat
    payload["has_visible_failure"] = provider.has_visible_failure
    return payload


def _emit_overview(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload))
        return

    print(f"providers={payload['provider_count']}")
    print(f"failed={payload['failed_provider_count']}")
    print(f"stale={payload['stale_provider_count']}")
    print(f"restricted={payload['restricted_provider_count']}")
    print(f"coverage={payload['total_coverage_count']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SahamLens provider health CLI.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List provider health overview.")
    p_list.set_defaults(func=cmd_list)

    p_yf = sub.add_parser("refresh-yfinance", help="Refresh yfinance OHLCV provider health.")
    p_yf.add_argument("--symbols", type=str, default="", help="Comma-separated tickers.")
    p_yf.add_argument("--from-watchlist", action="store_true", help="Use watchlist symbols.")
    p_yf.add_argument("--days", type=int, default=7, help="Fetch window size in days.")
    p_yf.set_defaults(func=cmd_refresh_yfinance)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
