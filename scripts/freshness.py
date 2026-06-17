"""Data freshness CLI — check and refresh stale data.

Usage:
  uv run python -m scripts.freshness check           # show freshness report
  uv run python -m scripts.freshness check --json    # machine-readable
  uv run python -m scripts.freshness refresh         # refresh all stale
  uv run python -m scripts.freshness refresh --type prices  # specific type
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime

from packages.core.runtime.freshness import FreshnessReport, check_freshness
from packages.core.schemas.repository import resolve_db_path


def cmd_check(args: argparse.Namespace) -> int:
    db_path = str(resolve_db_path(args.db))
    report = check_freshness(db_path)
    _emit(report, as_json=args.json)
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    db_path = str(resolve_db_path(args.db))
    report = check_freshness(db_path)

    stale = [t for t in report.stale_types if t == args.type] if args.type else report.stale_types

    if not stale:
        msg = {"ok": True, "message": "No stale data to refresh.", "refreshed": []}
        _emit(msg, as_json=args.json)
        return 0

    refreshed: list[str] = []
    errors: list[str] = []

    for data_type in stale:
        try:
            _run_refresh(data_type, db_path)
            refreshed.append(data_type)
        except Exception as exc:
            errors.append(f"{data_type}: {exc}")

    result = {
        "ok": not errors,
        "refreshed": refreshed,
        "errors": errors,
    }
    _emit(result, as_json=args.json)
    return 0 if not errors else 3


def _run_refresh(data_type: str, db_path: str) -> None:
    """Call the appropriate refresh script for a data type."""
    import subprocess
    import sys as _sys

    python = _sys.executable
    mapping = {
        "provider_health": ["-m", "scripts.provider_health", "refresh", "--json"],
        "prices": ["-m", "scripts.ingest_prices", "--from-watchlist", "--days", "7", "--json"],
        "news": ["-m", "scripts.ingest_news", "--from-watchlist", "--json"],
        "alerts": ["-m", "scripts.alerts", "evaluate", "--json"],
        "screener": [
            "-m",
            "scripts.screener",
            "run",
            "--builtin",
            "fundamentals-basic",
            "--from-watchlist",
            "--json",
        ],
        "strategy_rules": ["-m", "scripts.journal_review", "rules", "evaluate", "--json"],
        "weekly_review": ["-m", "scripts.journal_review", "review", "generate", "--json"],
    }
    cmd = mapping.get(data_type)
    if cmd is None:
        # fundamentals and ticker_coverage have no one-shot refresh script
        return
    result = subprocess.run(
        [python, *cmd],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode not in (0, 2):
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def _emit(report_or_dict: object, *, as_json: bool) -> None:
    if as_json:
        payload = report_or_dict
        if isinstance(report_or_dict, FreshnessReport):
            payload = _report_to_dict(report_or_dict)
        print(json.dumps(payload, default=str))
        return
    if isinstance(report_or_dict, FreshnessReport):
        _print_report(report_or_dict)
    else:
        print(report_or_dict)


def _report_to_dict(report: FreshnessReport) -> dict:
    return {
        "fresh_count": report.fresh_count,
        "stale_count": report.stale_count,
        "total_count": report.total_count,
        "has_stale": report.has_stale,
        "stale_types": report.stale_types,
        "records": [
            {
                "data_type": r.data_type,
                "status": r.status,
                "last_refreshed_at": r.last_refreshed_at,
                "age_seconds": r.age_seconds,
                "threshold_seconds": r.threshold_seconds,
            }
            for r in report.records
        ],
    }


def _print_report(report: FreshnessReport) -> None:
    now = datetime.now(UTC).isoformat(timespec="minutes")
    print(f"Freshness Report — {now}")
    print(
        f"  Total: {report.total_count}  Fresh: {report.fresh_count}  Stale: {report.stale_count}"
    )
    print()
    for r in report.records:
        icon = {"fresh": "✓", "stale": "✗", "unknown": "?"}.get(r.status, "?")
        age = ""
        if r.age_seconds is not None:
            minutes = int(r.age_seconds // 60)
            if minutes < 60:
                age = f" ({minutes}m ago)"
            else:
                age = f" ({minutes // 60}h {minutes % 60}m ago)"
        print(f"  {icon} {r.data_type:<20s} {r.status:<8s}{age}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Data freshness checker")
    parser.add_argument("--db", help="Path to DuckDB file (default: from env or default path)")
    parser.add_argument("--json", action="store_true", help="JSON output")

    sub = parser.add_subparsers(dest="command", required=True)

    check_parser = sub.add_parser("check", help="Show freshness report")
    check_parser.set_defaults(func=cmd_check)

    refresh_parser = sub.add_parser("refresh", help="Refresh stale data")
    refresh_parser.add_argument("--type", help="Refresh specific data type only")
    refresh_parser.set_defaults(func=cmd_refresh)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
