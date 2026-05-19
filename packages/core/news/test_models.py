"""Pydantic model invariants for news pipeline."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from packages.core.news.models import NewsArticle, NewsSummary
from pydantic import ValidationError


def test_news_article_auto_fills_id_from_url() -> None:
    a = NewsArticle(
        id=0,
        url="https://finance.detik.com/news/42",
        title="t",
        source="detik",
        published_at=datetime(2026, 5, 18, tzinfo=UTC),
        fetched_at=datetime(2026, 5, 18, tzinfo=UTC),
    )
    # id auto-populated via canonical url hash
    assert a.id > 0


def test_news_summary_canonicalizes_tickers() -> None:
    s = NewsSummary(
        news_id=1,
        url="https://x.com/a",
        summary="ringkasan singkat.",
        affected_tickers=["bbca", "TLKM.JK"],
        sentiment_label="neutral",
        caveats=["satu"],
        source_quality="reputable_media",
        confidence=0.9,
        not_financial_advice=True,
        prompt_template_id="news_summary.v1",
        model="claude-haiku-4-5-20251001",
        summarized_at=datetime(2026, 5, 18, tzinfo=UTC),
    )
    assert s.affected_tickers == ["BBCA.JK", "TLKM.JK"]


def test_news_summary_low_confidence_requires_caveats() -> None:
    with pytest.raises(ValidationError):
        NewsSummary(
            news_id=1,
            url="https://x.com/a",
            summary="ringkasan.",
            affected_tickers=[],
            sentiment_label="neutral",
            caveats=[],
            source_quality="unknown",
            confidence=0.5,
            not_financial_advice=True,
            prompt_template_id="news_summary.v1",
            model="m",
            summarized_at=datetime(2026, 5, 18, tzinfo=UTC),
        )


def test_news_summary_high_confidence_allows_empty_caveats() -> None:
    s = NewsSummary(
        news_id=1,
        url="https://x.com/a",
        summary="ok.",
        affected_tickers=[],
        sentiment_label="neutral",
        caveats=[],
        source_quality="unknown",
        confidence=0.85,
        not_financial_advice=True,
        prompt_template_id="news_summary.v1",
        model="m",
        summarized_at=datetime(2026, 5, 18, tzinfo=UTC),
    )
    assert s.caveats == []
