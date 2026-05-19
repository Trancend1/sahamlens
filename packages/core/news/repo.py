"""DuckDB persistence for news articles + AI summaries + audit log.

All upserts are idempotent via PRIMARY KEY conflicts. Connection is caller-managed.
"""

from __future__ import annotations

import json
import secrets
from collections.abc import Iterable
from datetime import UTC, datetime

import duckdb
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.news.models import NewsArticle, NewsSummary
from packages.core.news.rss_source import SOURCE_QUALITY


def upsert_news_articles(conn: duckdb.DuckDBPyConnection, articles: Iterable[NewsArticle]) -> int:
    """Insert raw articles; preserve existing row on URL conflict."""
    count = 0
    for article in articles:
        quality = SOURCE_QUALITY.get(article.source.lower(), "unknown")
        conn.execute(
            """
            INSERT INTO news
                (id, url, title, source, published_at, summary, affected_tickers,
                 sentiment_label, fetched_at, source_quality, confidence, caveats,
                 prompt_template_id, model, summarized_at)
            VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?, NULL, NULL, NULL, NULL, NULL)
            ON CONFLICT (id) DO NOTHING
            """,
            [
                article.id,
                article.url,
                article.title,
                article.source,
                article.published_at.isoformat(),
                article.fetched_at.isoformat(),
                quality,
            ],
        )
        count += 1
    return count


def upsert_news_summary(conn: duckdb.DuckDBPyConnection, summary: NewsSummary) -> None:
    """Update an existing news row with AI summary payload."""
    conn.execute(
        """
        UPDATE news SET
            summary = ?,
            affected_tickers = ?,
            sentiment_label = ?,
            source_quality = ?,
            confidence = ?,
            caveats = ?,
            prompt_template_id = ?,
            model = ?,
            summarized_at = ?
        WHERE id = ?
        """,
        [
            summary.summary,
            json.dumps(summary.affected_tickers),
            summary.sentiment_label,
            summary.source_quality,
            summary.confidence,
            json.dumps(summary.caveats),
            summary.prompt_template_id,
            summary.model,
            summary.summarized_at.isoformat(),
            summary.news_id,
        ],
    )


def load_recent_news_for_ticker(
    conn: duckdb.DuckDBPyConnection, symbol: str, *, limit: int = 5
) -> list[NewsSummary]:
    """Return up to N most recently published summaries that tagged this ticker."""
    canonical = normalize_ticker(symbol)
    needle = f'"{canonical}"'
    rows = conn.execute(
        """
        SELECT id, url, summary, affected_tickers, sentiment_label, caveats,
               source_quality, confidence, prompt_template_id, model, summarized_at
        FROM news
        WHERE summarized_at IS NOT NULL
          AND affected_tickers LIKE ?
        ORDER BY published_at DESC
        LIMIT ?
        """,
        [f"%{needle}%", limit],
    ).fetchall()
    summaries: list[NewsSummary] = []
    for r in rows:
        summaries.append(
            NewsSummary(
                news_id=int(r[0]),
                url=str(r[1]),
                summary=str(r[2]),
                affected_tickers=json.loads(r[3]) if r[3] else [],
                sentiment_label=r[4],
                caveats=json.loads(r[5]) if r[5] else [],
                source_quality=r[6] or "unknown",
                confidence=float(r[7]) if r[7] is not None else 0.0,
                not_financial_advice=True,
                prompt_template_id=str(r[8]) if r[8] else "",
                model=str(r[9]) if r[9] else "",
                summarized_at=datetime.fromisoformat(str(r[10])),
            )
        )
    return summaries


def load_news_lacking_summary(
    conn: duckdb.DuckDBPyConnection, *, limit: int = 20
) -> list[NewsArticle]:
    """Return raw articles awaiting summarization, oldest first."""
    rows = conn.execute(
        """
        SELECT id, url, title, source, published_at, fetched_at
        FROM news
        WHERE summarized_at IS NULL
        ORDER BY published_at ASC
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    return [
        NewsArticle(
            id=int(r[0]),
            url=str(r[1]),
            title=str(r[2]),
            source=str(r[3]) if r[3] else "unknown",
            published_at=datetime.fromisoformat(str(r[4])),
            fetched_at=datetime.fromisoformat(str(r[5])),
            raw_summary=None,
        )
        for r in rows
    ]


def log_ai_call(
    conn: duckdb.DuckDBPyConnection,
    *,
    prompt_template_id: str,
    model: str,
    input_context: str,
    output: str,
    confidence: float | None,
    caveats_count: int,
) -> int:
    """Append a row to `ai_log` audit trail. Returns generated id."""
    log_id = secrets.randbits(60)
    conn.execute(
        """
        INSERT INTO ai_log
            (id, prompt_template_id, model, input_context, output, confidence, caveats_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            log_id,
            prompt_template_id,
            model,
            input_context,
            output,
            confidence,
            caveats_count,
            datetime.now(UTC).isoformat(),
        ],
    )
    return log_id


def daily_ai_spend(conn: duckdb.DuckDBPyConnection, *, day_iso: str) -> int:
    """Return number of ai_log rows for a given UTC date (YYYY-MM-DD prefix match)."""
    row = conn.execute(
        "SELECT COUNT(*) FROM ai_log WHERE created_at LIKE ?",
        [f"{day_iso}%"],
    ).fetchone()
    return int(row[0]) if row else 0
