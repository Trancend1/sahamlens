"""Dump OHLCV + indicator series + latest indicator values for a symbol as JSON.

Single-call helper for stock detail page UI (apps/web/src/app/stocks/[symbol]).

Args:
  --symbol SYM      (required)
  --days N          last N price bars (default 365; pass 0 for full history)
  --db PATH         override DUCKDB_PATH
  --json            (default behavior; emitted unconditionally for CLI use by web)

Output JSON shape:
  {
    "symbol": "BBCA.JK",
    "ohlcv": [{"date":"YYYY-MM-DD","open":..,"high":..,"low":..,"close":..,"volume":..}, ...],
    "indicators_series": {
        "ma_5":  [{"date":"YYYY-MM-DD","value":..}, ...],
        ...10 keys...
    },
    "indicators_latest": {"ma_5": 1.0, ...},
    "first_date": "YYYY-MM-DD",
    "last_date":  "YYYY-MM-DD",
    "news_recent": [{"news_id":..,"url":..,"summary":..,"affected_tickers":[..],
                     "sentiment_label":..,"caveats":[..],"source_quality":..,
                     "confidence":..,"summarized_at":..}, ...]
  }

Exit code: 0 ok, 2 empty (no price rows for symbol), 3 error.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import TypedDict

import duckdb
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.indicators import INDICATOR_KEYS, latest_for
from packages.core.news.repo import load_recent_news_for_ticker
from packages.core.schemas.repository import OHLCVRow, load_ohlcv, open_connection

EXIT_OK = 0
EXIT_EMPTY = 2
EXIT_ERROR = 3


class IndicatorSeriesPoint(TypedDict):
    date: str
    value: float


class NewsRecent(TypedDict):
    news_id: int
    url: str
    summary: str
    affected_tickers: list[str]
    sentiment_label: str
    caveats: list[str]
    source_quality: str
    confidence: float
    summarized_at: str


class StockDetailPayload(TypedDict):
    symbol: str
    ohlcv: list[OHLCVRow]
    indicators_series: dict[str, list[IndicatorSeriesPoint]]
    indicators_latest: dict[str, float]
    first_date: str | None
    last_date: str | None
    news_recent: list[NewsRecent]


def load_news_recent(conn: duckdb.DuckDBPyConnection, symbol: str) -> list[NewsRecent]:
    summaries = load_recent_news_for_ticker(conn, symbol, limit=5)
    return [
        NewsRecent(
            news_id=s.news_id,
            url=s.url,
            summary=s.summary,
            affected_tickers=list(s.affected_tickers),
            sentiment_label=s.sentiment_label,
            caveats=list(s.caveats),
            source_quality=s.source_quality,
            confidence=s.confidence,
            summarized_at=s.summarized_at.isoformat(),
        )
        for s in summaries
    ]


def load_indicator_series(
    conn: duckdb.DuckDBPyConnection, symbol: str, *, first_date: str | None
) -> dict[str, list[IndicatorSeriesPoint]]:
    canonical = normalize_ticker(symbol)
    series: dict[str, list[IndicatorSeriesPoint]] = {key: [] for key in INDICATOR_KEYS}
    if first_date is None:
        return series
    rows = conn.execute(
        """
        SELECT indicator, date, value
        FROM indicator_cache
        WHERE symbol = ? AND date >= ?
        ORDER BY date
        """,
        [canonical, first_date],
    ).fetchall()
    for ind, d, v in rows:
        if ind in series:
            series[ind].append({"date": str(d), "value": float(v)})
    return series


def build_payload(
    conn: duckdb.DuckDBPyConnection, symbol: str, *, limit: int | None
) -> StockDetailPayload:
    canonical = normalize_ticker(symbol)
    ohlcv = load_ohlcv(conn, canonical, limit=limit)
    first = ohlcv[0]["date"] if ohlcv else None
    last = ohlcv[-1]["date"] if ohlcv else None
    series = load_indicator_series(conn, canonical, first_date=first)
    latest = latest_for(conn, canonical)
    news_recent = load_news_recent(conn, canonical)
    return {
        "symbol": canonical,
        "ohlcv": ohlcv,
        "indicators_series": series,
        "indicators_latest": latest,
        "first_date": first,
        "last_date": last,
        "news_recent": news_recent,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dump stock detail payload as JSON.")
    parser.add_argument("--symbol", type=str, required=True, help="IDX ticker (e.g. BBCA).")
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Trailing N price rows (default 365; pass 0 for full history).",
    )
    parser.add_argument("--db", type=str, default=None, help="Override DUCKDB_PATH.")
    args = parser.parse_args(argv)

    limit = args.days if args.days > 0 else None

    try:
        with open_connection(args.db) as conn:
            payload = build_payload(conn, args.symbol, limit=limit)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return EXIT_ERROR

    print(json.dumps(payload, default=str))
    if not payload["ohlcv"]:
        return EXIT_EMPTY
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
