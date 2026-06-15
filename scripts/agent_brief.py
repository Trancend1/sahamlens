"""Agent brief CLI (ADR-0019 M0) — pull-only outbound brief, no runtime.

Generates a StockBrief by reusing packages.core.ai.generate_stock_brief, formats
it with the neutral agent wrapper, prints it, and optionally sends it outbound to
Telegram (existing telegram.py). Owner-triggered; there is no long-running
process. Telegram is optional: without config the brief is printed only.

Examples:
  uv run python -m scripts.agent_brief --symbol BBCA
  uv run python -m scripts.agent_brief --symbol BBCA --send
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from packages.core.agent.brief_delivery import format_brief_message
from packages.core.ai.generate_brief import generate_stock_brief
from packages.core.ai.provider import resolve_provider
from packages.core.ai.router import CircuitBreaker, ModelRouter, load_budget
from packages.core.alerts.telegram import get_telegram_status, send_text_to_telegram
from packages.core.schemas.repository import open_connection

EXIT_OK = 0
EXIT_UNAVAILABLE = 3
EXIT_DELIVERY_FAILED = 4


def cmd_brief(args: argparse.Namespace) -> int:
    provider = resolve_provider()
    router = ModelRouter()
    breaker = CircuitBreaker(load_budget())
    with open_connection(args.db) as conn:
        brief = generate_stock_brief(
            args.symbol,
            provider=provider,
            router=router,
            breaker=breaker,
            conn=conn,
        )
    if brief is None:
        print("brief unavailable (budget exceeded, provider error, or validation failure)")
        return EXIT_UNAVAILABLE

    message = format_brief_message(brief)
    print(message)

    if not args.send:
        return EXIT_OK

    status = get_telegram_status()
    if not status.configured:
        print("\n[telegram] not configured — printed only, nothing sent.")
        return EXIT_OK

    response = send_text_to_telegram(message)
    if not response.ok:
        print(f"\n[telegram] delivery failed: {response.error_code}")
        return EXIT_DELIVERY_FAILED
    print("\n[telegram] sent.")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SahamLens agent brief (pull-only).")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--symbol", type=str, required=True, help="IDX ticker (e.g. BBCA).")
    parser.add_argument(
        "--send",
        action="store_true",
        help="Also send the brief outbound to Telegram if configured.",
    )
    parser.set_defaults(func=cmd_brief)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
