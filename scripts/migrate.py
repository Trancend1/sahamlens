"""Apply pending DuckDB migrations from packages/core/schemas/migrations/.

Idempotent: tracks applied versions in `schema_migrations` table.
Usage: `uv run python -m scripts.migrate [--db PATH]`
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import duckdb
from dotenv import load_dotenv

MIGRATIONS_DIR = (
    Path(__file__).resolve().parent.parent / "packages" / "core" / "schemas" / "migrations"
)
DEFAULT_DB = "./data/private/sahamlens.duckdb"


def resolve_db_path(cli_path: str | None) -> Path:
    load_dotenv(".env.local")
    raw = cli_path or os.environ.get("DUCKDB_PATH", DEFAULT_DB)
    path = Path(raw).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def discover_migrations() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql"))


def applied_versions(conn: duckdb.DuckDBPyConnection) -> set[str]:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def apply_migration(conn: duckdb.DuckDBPyConnection, path: Path) -> None:
    version = path.stem.split("_", 1)[0]
    sql = path.read_text(encoding="utf-8")
    conn.execute(sql)
    conn.execute(
        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
        [version, datetime.now(UTC).isoformat()],
    )
    print(f"applied {path.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply DuckDB migrations.")
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    args = parser.parse_args()

    db_path = resolve_db_path(args.db)
    migrations = discover_migrations()
    if not migrations:
        print(f"no migrations found in {MIGRATIONS_DIR}")
        return 0

    with duckdb.connect(str(db_path)) as conn:
        already = applied_versions(conn)
        pending = [p for p in migrations if p.stem.split("_", 1)[0] not in already]
        if not pending:
            print(f"up to date ({len(already)} migration(s) applied)")
            return 0
        for path in pending:
            apply_migration(conn, path)
        print(f"done ({len(pending)} new migration(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
