"""Local runtime readiness and bootstrap CLI.

Examples:
  uv run python -m scripts.runtime status --json
  uv run python -m scripts.runtime bootstrap --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from packages.core.runtime import (
    BootstrapResult,
    BootstrapStep,
    RuntimeWarning,
    get_runtime_status,
    run_runtime_bootstrap,
)
from packages.core.schemas.repository import open_connection
from packages.core.watchlist import list_entries


def cmd_status(args: argparse.Namespace) -> int:
    status = get_runtime_status(args.db)
    _emit(status.model_dump(mode="json"), as_json=args.json)
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    result = run_runtime_bootstrap(args.db)
    result = _run_optional_data_bootstrap(args.db, result)
    _emit(result.model_dump(mode="json"), as_json=args.json)
    return 0 if result.status.schema_status == "ready" else 3


def _emit(payload: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload))
        return
    print(payload)


def _run_optional_data_bootstrap(
    db_path: str | None,
    result: BootstrapResult,
) -> BootstrapResult:
    if result.status.schema_status != "ready":
        return result

    with open_connection(db_path, read_only=True) as conn:
        symbols = [entry.symbol for entry in list_entries(conn)]
    if not symbols:
        return result
    result.steps.extend(_refresh_provider_health(db_path, symbols))
    result.steps.extend(_refresh_coverage(db_path, symbols))
    result.steps.extend(_run_screener(db_path, symbols))

    status = get_runtime_status(db_path)
    warnings = [*status.warnings]
    for step in result.steps:
        if step.status in {"skipped", "warning", "failed"}:
            warnings.append(
                RuntimeWarning(
                    code=f"bootstrap_{step.status}",
                    message=f"{step.name}: {step.message}",
                    recommended_command=step.recommended_command,
                )
            )
    return BootstrapResult(
        ok=status.schema_status == "ready"
        and not any(step.status == "failed" for step in result.steps),
        steps=result.steps,
        status=status,
        warnings=warnings,
        errors=status.errors,
        recommended_commands=[
            *status.recommended_commands,
            *[
                step.recommended_command
                for step in result.steps
                if step.recommended_command is not None
            ],
        ],
    )


def _refresh_provider_health(db_path: str | None, symbols: list[str]) -> list[BootstrapStep]:
    try:
        from packages.core.data_quality.repo import upsert_provider_health_snapshot
        from packages.core.data_sources.yfinance import YFinanceSource

        from scripts.provider_health import fetch_yfinance_provider_health_snapshot

        end = datetime.now(UTC).date()
        start = end - timedelta(days=7)
        snapshot = fetch_yfinance_provider_health_snapshot(
            YFinanceSource(),
            symbols,
            start=start,
            end=end,
        )
        with open_connection(db_path) as conn:
            upsert_provider_health_snapshot(conn, snapshot)
        return [
            BootstrapStep(
                name="provider_health",
                status="completed",
                message=f"Refreshed yfinance provider health for {len(symbols)} symbol(s).",
            )
        ]
    except Exception as exc:
        return [
            BootstrapStep(
                name="provider_health",
                status="warning",
                message=f"Provider health refresh did not complete: {exc}",
                recommended_command=(
                    "uv run python -m scripts.provider_health --json refresh-yfinance --from-watchlist"
                ),
            )
        ]


def _refresh_coverage(db_path: str | None, symbols: list[str]) -> list[BootstrapStep]:
    try:
        from scripts.fundamentals import refresh_ticker_coverage

        with open_connection(db_path) as conn:
            refresh_ticker_coverage(
                conn,
                symbols,
                lifecycle_status="active",
                checked_at=datetime.now(UTC),
            )
        return [
            BootstrapStep(
                name="coverage_fundamentals",
                status="completed",
                message=f"Refreshed coverage for {len(symbols)} symbol(s).",
            )
        ]
    except Exception as exc:
        return [
            BootstrapStep(
                name="coverage_fundamentals",
                status="warning",
                message=f"Coverage/fundamental refresh did not complete: {exc}",
                recommended_command=(
                    "uv run python -m scripts.fundamentals --json refresh-coverage --from-watchlist"
                ),
            )
        ]


def _run_screener(db_path: str | None, symbols: list[str]) -> list[BootstrapStep]:
    try:
        from packages.core.screener import evaluate_screener_rule, upsert_screener_run

        from scripts.screener import _load_candidates, fundamentals_basic_rule

        rule = fundamentals_basic_rule()
        with open_connection(db_path) as conn:
            run = evaluate_screener_rule(
                rule,
                _load_candidates(conn, symbols),
                run_id=f"bootstrap-screener-{uuid4().hex}",
                evaluated_at=datetime.now(UTC),
            )
            upsert_screener_run(conn, run)
        return [
            BootstrapStep(
                name="screener",
                status="completed",
                message=f"Persisted screener run for {len(symbols)} symbol(s).",
            )
        ]
    except Exception as exc:
        return [
            BootstrapStep(
                name="screener",
                status="warning",
                message=f"Screener run did not complete: {exc}",
                recommended_command=(
                    "uv run python -m scripts.screener --json run --builtin fundamentals-basic --from-watchlist"
                ),
            )
        ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SahamLens local runtime readiness CLI.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_status = sub.add_parser("status", help="Inspect local runtime readiness.")
    p_status.add_argument("--json", action="store_true", help="Emit JSON to stdout.")
    p_status.set_defaults(func=cmd_status)

    p_bootstrap = sub.add_parser("bootstrap", help="Apply safe local bootstrap steps.")
    p_bootstrap.add_argument("--json", action="store_true", help="Emit JSON to stdout.")
    p_bootstrap.set_defaults(func=cmd_bootstrap)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
