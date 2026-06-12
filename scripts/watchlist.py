"""Watchlist CLI: add / remove / list / seed.

Examples:
  uv run python -m scripts.watchlist list --json
  uv run python -m scripts.watchlist add BBCA --tag bank-core --note "Big bank"
  uv run python -m scripts.watchlist remove BBCA
  uv run python -m scripts.watchlist seed
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

from packages.core.schemas.repository import open_connection
from packages.core.watchlist import (
    WatchlistAlreadyExists,
    WatchlistNotFound,
    add_entry,
    list_entries,
    remove_entry,
)

DEFAULT_SEED = Path(__file__).resolve().parent.parent / "data" / "sample" / "sample_watchlist.csv"


def cmd_list(args: argparse.Namespace) -> int:
    with open_connection(args.db, read_only=True) as conn:
        entries = [e.model_dump(mode="json") for e in list_entries(conn)]
    if args.json:
        print(json.dumps(entries))
    else:
        if not entries:
            print("(empty)")
            return 0
        for e in entries:
            tag = f"  [{e['tag']}]" if e["tag"] else ""
            print(f"{e['symbol']}{tag}  added {e['added_at']}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    with open_connection(args.db) as conn:
        try:
            entry = add_entry(conn, args.symbol, tag=args.tag, note=args.note)
        except WatchlistAlreadyExists as exc:
            print(f"already exists: {exc}", file=sys.stderr)
            return 1
    if args.json:
        print(json.dumps(entry.model_dump(mode="json")))
    else:
        print(f"added {entry.symbol}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    with open_connection(args.db) as conn:
        try:
            remove_entry(conn, args.symbol)
        except WatchlistNotFound as exc:
            print(f"not found: {exc}", file=sys.stderr)
            return 1
    print(f"removed {args.symbol}")
    return 0


def cmd_seed(args: argparse.Namespace) -> int:
    csv_path = Path(args.csv) if args.csv else DEFAULT_SEED
    if not csv_path.exists():
        print(f"seed csv not found: {csv_path}", file=sys.stderr)
        return 1
    added: list[str] = []
    skipped: list[str] = []
    with open_connection(args.db) as conn, csv_path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(_strip_comments(fh))
        for row in reader:
            try:
                entry = add_entry(
                    conn,
                    row["symbol"],
                    tag=row.get("tag") or None,
                    note=row.get("note") or None,
                )
                added.append(entry.symbol)
            except WatchlistAlreadyExists:
                skipped.append(row["symbol"])
    if args.json:
        print(json.dumps({"added": added, "skipped": skipped}))
    else:
        print(f"added: {added}")
        print(f"skipped (already present): {skipped}")
    return 0


def _strip_comments(lines: Iterable[str]) -> Iterator[str]:
    for line in lines:
        if line.lstrip().startswith("#"):
            continue
        yield line


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SahamLens watchlist CLI.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List entries.")
    p_list.set_defaults(func=cmd_list)

    p_add = sub.add_parser("add", help="Add ticker.")
    p_add.add_argument("symbol")
    p_add.add_argument("--tag", default=None)
    p_add.add_argument("--note", default=None)
    p_add.set_defaults(func=cmd_add)

    p_rm = sub.add_parser("remove", help="Remove ticker.")
    p_rm.add_argument("symbol")
    p_rm.set_defaults(func=cmd_remove)

    p_seed = sub.add_parser("seed", help="Seed from data/sample/sample_watchlist.csv.")
    p_seed.add_argument("--csv", default=None, help="Override seed CSV path.")
    p_seed.set_defaults(func=cmd_seed)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
