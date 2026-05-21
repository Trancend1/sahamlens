"""RAG context builder for stock analysis.

Assembles structured context from local DuckDB for use as LLM prompt context.
Architecture: AI_BOUNDARIES.md §4.1 — every AI output must be based on retrieved data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import duckdb
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.indicators import latest_for
from packages.core.journal.repo import list_plans
from packages.core.news.repo import load_recent_news_for_ticker
from packages.core.schemas.repository import load_ohlcv


@dataclass
class PriceContext:
    symbol: str
    last_close: float
    prev_close: float
    change_pct: float
    high_90d: float
    low_90d: float
    last_date: str


@dataclass
class StockContext:
    symbol: str
    price: PriceContext | None
    indicators: dict[str, float]
    news: list[dict[str, Any]]
    journal_plans: list[dict[str, Any]]
    last_date: str | None

    def as_text(self) -> str:
        """Format context as human-readable text for LLM prompt injection."""
        lines: list[str] = []

        if self.price:
            p = self.price
            direction = "+" if p.change_pct >= 0 else ""
            lines.append(
                f"Harga terakhir ({p.last_date}): {p.last_close:,.0f} "
                f"({direction}{p.change_pct:.2f}% dari hari sebelumnya). "
                f"Range 90 hari: low {p.low_90d:,.0f} / high {p.high_90d:,.0f}."
            )
        else:
            lines.append("Harga: tidak tersedia.")

        if self.indicators:
            ind_parts: list[str] = []
            for k, v in self.indicators.items():
                ind_parts.append(f"{k}={v:.2f}" if v else f"{k}=n/a")
            lines.append("Indikator: " + ", ".join(ind_parts) + ".")
        else:
            lines.append("Indikator: belum dihitung.")

        if self.news:
            lines.append(f"Berita terbaru ({len(self.news)} artikel):")
            for n in self.news:
                sentiment = n.get("sentiment_label", "unknown")
                summary = n.get("summary", "")
                summarized = n.get("summarized_at", "")
                lines.append(f"  [{sentiment}] {summary} (di-summarize: {summarized})")
        else:
            lines.append("Berita: tidak ada berita terbaru.")

        if self.journal_plans:
            lines.append(f"Journal plans aktif ({len(self.journal_plans)} plan):")
            for jp in self.journal_plans:
                status = jp.get("status", "")
                setup = jp.get("setup_type", "")
                thesis = jp.get("thesis", "")
                lines.append(f"  [{status}/{setup}] {thesis}")
        else:
            lines.append("Journal: tidak ada plan aktif untuk saham ini.")

        return "\n".join(lines)


def build_stock_context(
    conn: duckdb.DuckDBPyConnection,
    symbol: str,
    *,
    limit_days: int = 90,
) -> StockContext:
    """Build structured context for a symbol from DuckDB."""
    canonical = normalize_ticker(symbol)

    ohlcv = load_ohlcv(conn, canonical, limit=limit_days)

    price_ctx: PriceContext | None = None
    if len(ohlcv) >= 2:
        last = ohlcv[-1]
        prev = ohlcv[-2]
        if last["close"] is not None and prev["close"] is not None:
            last_close = float(last["close"])
            prev_close = float(prev["close"])
            change_pct = ((last_close - prev_close) / prev_close) * 100 if prev_close else 0.0
            highs = [h for r in ohlcv if (h := r["high"]) is not None]
            lows = [lo for r in ohlcv if (lo := r["low"]) is not None]
            price_ctx = PriceContext(
                symbol=canonical,
                last_close=last_close,
                prev_close=prev_close,
                change_pct=change_pct,
                high_90d=max(highs) if highs else last_close,
                low_90d=min(lows) if lows else last_close,
                last_date=str(last["date"]),
            )

    indicators = latest_for(conn, canonical)

    news_raw = load_recent_news_for_ticker(conn, canonical, limit=3)
    news: list[dict[str, Any]] = [
        {
            "sentiment_label": n.sentiment_label,
            "summary": n.summary,
            "source_quality": n.source_quality,
            "confidence": n.confidence,
            "summarized_at": n.summarized_at.isoformat(),
        }
        for n in news_raw
    ]

    plans_raw = list_plans(conn, symbol=canonical, status="planned")
    plans_open = list_plans(conn, symbol=canonical, status="open")
    journal_plans: list[dict[str, Any]] = [
        {"status": p.status, "setup_type": p.setup_type, "thesis": p.thesis}
        for p in (*plans_raw, *plans_open)
    ]

    last_date = ohlcv[-1]["date"] if ohlcv else None
    return StockContext(
        symbol=canonical,
        price=price_ctx,
        indicators=indicators,
        news=news,
        journal_plans=journal_plans,
        last_date=str(last_date) if last_date else None,
    )
