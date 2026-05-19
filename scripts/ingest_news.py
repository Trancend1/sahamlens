"""Fetch RSS news from configured sources, dedup, and upsert raw articles.

Sources resolved from `config/rss_feeds.yml` (falls back to `.example.yml`).

Usage:
  uv run python -m scripts.ingest_news
  uv run python -m scripts.ingest_news --sources detik,cnbc --json
  uv run python -m scripts.ingest_news --since 2026-05-12T00:00:00
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import yaml
from packages.core.news.models import FetchNewsResult
from packages.core.news.pipeline import ingest_news
from packages.core.news.rss_source import RSSNewsSource
from packages.core.schemas.repository import open_connection

EXIT_OK = 0
EXIT_PARTIAL = 2
EXIT_FAILED = 3

DEFAULT_CONFIG = Path("config/rss_feeds.yml")
EXAMPLE_CONFIG = Path("config/rss_feeds.example.yml")


def load_feed_urls(*, selected: list[str] | None) -> dict[str, str]:
    target = DEFAULT_CONFIG if DEFAULT_CONFIG.exists() else EXAMPLE_CONFIG
    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    sources = raw.get("sources", {})
    if not isinstance(sources, dict):
        raise ValueError(f"invalid rss config at {target}: missing 'sources' mapping")
    feeds = {str(k): str(v) for k, v in sources.items() if isinstance(v, str)}
    if selected:
        return {k: v for k, v in feeds.items() if k in selected}
    return feeds


class Summary(TypedDict):
    articles_seen: int
    by_status: dict[str, list[str]]
    errors: dict[str, str]


def summarize(results: Sequence[FetchNewsResult]) -> Summary:
    return {
        "articles_seen": sum(len(r.articles) for r in results),
        "by_status": {
            "ok": [r.source for r in results if r.status == "ok"],
            "partial": [r.source for r in results if r.status == "partial"],
            "failed": [r.source for r in results if r.status == "failed"],
        },
        "errors": {r.source: r.error_message for r in results if r.error_message},
    }


def exit_code(results: Sequence[FetchNewsResult]) -> int:
    if any(r.status == "failed" for r in results):
        return EXIT_FAILED
    if any(r.status == "partial" for r in results):
        return EXIT_PARTIAL
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest IDX news RSS feeds into DuckDB.")
    parser.add_argument("--sources", type=str, default="", help="Comma-separated source labels.")
    parser.add_argument("--since", type=str, default=None, help="ISO datetime cutoff.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")
    args = parser.parse_args(argv)

    selected = [s.strip() for s in (args.sources or "").split(",") if s.strip()] or None
    since = datetime.fromisoformat(args.since) if args.since else None

    try:
        feeds = load_feed_urls(selected=selected)
    except (FileNotFoundError, ValueError) as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return EXIT_FAILED

    if not feeds:
        print("no feeds resolved (check --sources vs config)", file=sys.stderr)
        return EXIT_FAILED

    source = RSSNewsSource(feeds)
    with open_connection(args.db) as conn:
        results = ingest_news(conn, source, since=since)

    summary = summarize(results)
    if args.json:
        print(json.dumps(summary, default=str))
    else:
        print(f"articles_seen={summary['articles_seen']}")
        print(f"ok={summary['by_status']['ok']}")
        print(f"partial={summary['by_status']['partial']}")
        print(f"failed={summary['by_status']['failed']}")
        for label, msg in summary["errors"].items():
            print(f"  {label}: {msg}", file=sys.stderr)

    return exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
