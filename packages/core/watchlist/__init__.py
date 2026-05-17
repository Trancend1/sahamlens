"""Watchlist module: focused candidate pool (separate from journal which records trades).

CRUD over DuckDB `watchlist` table. Owner-injectable connection so callers control DB path.
"""

from packages.core.watchlist.repo import (
    WatchlistAlreadyExists,
    WatchlistNotFound,
    add_entry,
    get_entry,
    list_entries,
    remove_entry,
)

__all__ = [
    "WatchlistAlreadyExists",
    "WatchlistNotFound",
    "add_entry",
    "get_entry",
    "list_entries",
    "remove_entry",
]
