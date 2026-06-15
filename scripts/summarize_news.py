"""Summarize pending news articles via the LLM wrapper.

Reads articles where `summarized_at IS NULL`, calls the AI summarizer, validates,
and writes the structured summary back into the `news` row.

Usage:
  uv run python -m scripts.summarize_news --limit 20
  uv run python -m scripts.summarize_news --from-watchlist --json
  uv run python -m scripts.summarize_news --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from typing import TypedDict

import duckdb
from packages.core.ai.provider import resolve_provider
from packages.core.ai.router import CircuitBreaker, ModelRouter, load_budget
from packages.core.ai.summarize_news import summarize_news
from packages.core.news.models import NewsArticle, NewsSummary
from packages.core.news.pipeline import summarize_pending
from packages.core.news.repo import load_news_lacking_summary
from packages.core.schemas.repository import open_connection
from packages.core.watchlist import list_entries

SummarizerFn = Callable[[NewsArticle, list[str]], NewsSummary | None]

EXIT_OK = 0
EXIT_PARTIAL = 2
EXIT_FAILED = 3


class Summary(TypedDict):
    succeeded: int
    failed: int
    dry_run: bool
    errors: dict[str, str]


def _resolve_watchlist(conn: duckdb.DuckDBPyConnection, *, from_watchlist: bool) -> list[str]:
    if not from_watchlist:
        return []
    return [e.symbol for e in list_entries(conn)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize pending news via LLM.")
    parser.add_argument("--limit", type=int, default=20, help="Max articles per run.")
    parser.add_argument(
        "--from-watchlist", action="store_true", help="Use watchlist tickers as context."
    )
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline but do not persist.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")
    args = parser.parse_args(argv)

    budget = load_budget()
    provider = resolve_provider()
    router = ModelRouter()
    breaker = CircuitBreaker(budget)

    errors: dict[str, str] = {}

    def summarizer(article: NewsArticle, watchlist: list[str]) -> NewsSummary | None:
        try:
            result = summarize_news(
                article,
                watchlist=watchlist,
                provider=provider,
                router=router,
                breaker=breaker,
                conn=conn,
            )
        except Exception as exc:  # never raise through CLI
            errors[str(article.id)] = str(exc)
            return None
        if result is None:
            errors[str(article.id)] = "summarizer returned None"
        return result

    with open_connection(args.db) as conn:
        watchlist = _resolve_watchlist(conn, from_watchlist=args.from_watchlist)
        if args.dry_run:
            succeeded, failed = _run_dry(conn, summarizer, watchlist=watchlist, limit=args.limit)
        else:
            succeeded, failed = summarize_pending(
                conn, summarizer, watchlist=watchlist, limit=args.limit
            )

    summary: Summary = {
        "succeeded": succeeded,
        "failed": failed,
        "dry_run": args.dry_run,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(summary, default=str))
    else:
        print(f"succeeded={succeeded} failed={failed} dry_run={args.dry_run}")
        for art_id, msg in errors.items():
            print(f"  {art_id}: {msg}", file=sys.stderr)

    if failed and succeeded == 0:
        return EXIT_FAILED
    if failed:
        return EXIT_PARTIAL
    return EXIT_OK


def _run_dry(
    conn: duckdb.DuckDBPyConnection,
    summarizer: SummarizerFn,
    *,
    watchlist: list[str],
    limit: int,
) -> tuple[int, int]:
    """Same flow as summarize_pending but without upsert_news_summary."""
    succeeded = 0
    failed = 0
    pending = load_news_lacking_summary(conn, limit=limit)
    for article in pending:
        result = summarizer(article, watchlist)
        if result is None:
            failed += 1
        else:
            succeeded += 1
    return succeeded, failed


if __name__ == "__main__":
    sys.exit(main())
