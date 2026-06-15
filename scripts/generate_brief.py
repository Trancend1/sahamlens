"""Generate stock brief CLI.

Examples:
  uv run python -m scripts.generate_brief --symbol BBCA
  uv run python -m scripts.generate_brief --symbol BBCA --db path/to/db.duckdb
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from packages.core.ai.generate_brief import generate_stock_brief
from packages.core.ai.provider import resolve_provider
from packages.core.ai.router import CircuitBreaker, ModelRouter, load_budget
from packages.core.ai.stock_chat import answer_stock_question
from packages.core.schemas.repository import open_connection

EXIT_OK = 0
EXIT_NOT_FOUND = 2
EXIT_UNAVAILABLE = 3


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
        print(json.dumps({"error": "brief unavailable"}))
        return EXIT_UNAVAILABLE
    print(json.dumps(brief.model_dump(mode="json")))
    return EXIT_OK


def cmd_chat(args: argparse.Namespace) -> int:
    provider = resolve_provider()
    router = ModelRouter()
    breaker = CircuitBreaker(load_budget())
    with open_connection(args.db) as conn:
        response = answer_stock_question(
            args.question,
            args.symbol,
            provider=provider,
            router=router,
            breaker=breaker,
            conn=conn,
        )
    if response is None:
        print(json.dumps({"error": "chat unavailable"}))
        return EXIT_UNAVAILABLE
    print(json.dumps(response.model_dump(mode="json")))
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SahamLens stock brief + chat CLI.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_brief = sub.add_parser("brief", help="Generate stock analysis brief.")
    p_brief.add_argument("--symbol", type=str, required=True, help="IDX ticker (e.g. BBCA).")
    p_brief.set_defaults(func=cmd_brief)

    p_chat = sub.add_parser("chat", help="Ask a contextual question about a stock.")
    p_chat.add_argument("--symbol", type=str, required=True, help="IDX ticker (e.g. BBCA).")
    p_chat.add_argument("--question", type=str, required=True, help="Question text.")
    p_chat.set_defaults(func=cmd_chat)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
