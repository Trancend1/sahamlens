"""Portfolio CLI: list positions and import from CSV.

Examples:
  uv run python -m scripts.portfolio list
  uv run python -m scripts.portfolio parse --csv-content "symbol,lots,avg_price\nBBCA,10,9200"
  uv run python -m scripts.portfolio save --positions '[{"symbol":"BBCA.JK","lots":10,...}]'
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from packages.core.portfolio.csv_importer import parse_csv
from packages.core.portfolio.models import PortfolioPosition
from packages.core.portfolio.repo import list_positions, replace_positions
from packages.core.schemas.repository import open_connection


def cmd_list(args: argparse.Namespace) -> int:
    with open_connection(read_only=True) as conn:
        positions = list_positions(conn)
    print(
        json.dumps(
            [
                {
                    "symbol": p.symbol,
                    "lots": p.lots,
                    "avg_price": p.avg_price,
                    "imported_at": p.imported_at.isoformat(),
                    "source": p.source,
                }
                for p in positions
            ]
        )
    )
    return 0


def cmd_parse(args: argparse.Namespace) -> int:
    field_map: dict[str, str] | None = None
    if args.field_map:
        try:
            field_map = json.loads(args.field_map)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"field_map JSON invalid: {e}"}))
            return 1

    result = parse_csv(args.csv_content, field_map=field_map)
    print(
        json.dumps(
            {
                "positions": [
                    {
                        "symbol": p.symbol,
                        "lots": p.lots,
                        "avg_price": p.avg_price,
                        "imported_at": p.imported_at.isoformat(),
                        "source": p.source,
                    }
                    for p in result.positions
                ],
                "warnings": result.warnings,
                "field_map": result.field_map,
                "detected_columns": result.detected_columns,
            }
        )
    )
    return 0 if not result.warnings or result.positions else 1


def cmd_save(args: argparse.Namespace) -> int:
    try:
        raw: list[dict[str, Any]] = json.loads(args.positions)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"positions JSON invalid: {e}"}))
        return 1

    now = datetime.now(UTC)
    positions: list[PortfolioPosition] = []
    for row in raw:
        try:
            positions.append(
                PortfolioPosition(
                    symbol=row["symbol"],
                    lots=int(row["lots"]),
                    avg_price=float(row["avg_price"]),
                    imported_at=datetime.fromisoformat(
                        str(row.get("imported_at") or now.isoformat())
                    ),
                    source=row.get("source", "csv"),
                )
            )
        except (KeyError, ValueError) as e:
            print(json.dumps({"error": f"invalid position row: {e}"}))
            return 1

    with open_connection() as conn:
        count = replace_positions(conn, positions)

    print(json.dumps({"saved": count}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="portfolio")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    parse_p = sub.add_parser("parse")
    parse_p.add_argument("--csv-content", required=True)
    parse_p.add_argument("--field-map", default=None)

    save_p = sub.add_parser("save")
    save_p.add_argument("--positions", required=True)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dispatch = {"list": cmd_list, "parse": cmd_parse, "save": cmd_save}
    return dispatch[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
