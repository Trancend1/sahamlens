"""News pipeline: RSS ingest + dedup + AI summarization wiring.

Public surface stays narrow — most consumers only need the high-level entry points.
"""

from packages.core.news.dedup import article_id, canonical_url
from packages.core.news.models import FetchNewsResult, NewsArticle, NewsSummary
from packages.core.news.pipeline import ingest_news, summarize_pending
from packages.core.news.repo import (
    load_news_lacking_summary,
    load_recent_news_for_ticker,
    log_ai_call,
    upsert_news_articles,
    upsert_news_summary,
)
from packages.core.news.rss_source import SOURCE_QUALITY, RSSNewsSource

__all__ = [
    "SOURCE_QUALITY",
    "FetchNewsResult",
    "NewsArticle",
    "NewsSummary",
    "RSSNewsSource",
    "article_id",
    "canonical_url",
    "ingest_news",
    "load_news_lacking_summary",
    "load_recent_news_for_ticker",
    "log_ai_call",
    "summarize_pending",
    "upsert_news_articles",
    "upsert_news_summary",
]
