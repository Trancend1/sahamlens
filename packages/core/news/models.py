"""Pydantic models for the news pipeline.

`NewsArticle` = raw fetched item. `NewsSummary` = AI-validated output (AI_BOUNDARIES §3.3).
`FetchNewsResult` mirrors `FetchResult` shape from `packages/core/schemas/models.py`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from packages.core.data_sources.normalize import normalize_ticker
from packages.core.news.dedup import article_id, canonical_url
from packages.core.schemas.models import FetchStatus
from pydantic import BaseModel, Field, field_validator, model_validator

SentimentLabel = Literal["bullish", "neutral", "bearish", "mixed"]
SourceQuality = Literal["official", "reputable_media", "blog", "unknown"]


class NewsArticle(BaseModel):
    """Raw fetched news row. `id` auto-derives from canonical url when not supplied."""

    id: int
    url: str
    title: str
    source: str
    published_at: datetime
    fetched_at: datetime
    raw_summary: str | None = None

    @field_validator("url")
    @classmethod
    def _canonicalize(cls, v: str) -> str:
        return canonical_url(v)

    @model_validator(mode="before")
    @classmethod
    def _fill_id(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        url_raw = data.get("url")
        if isinstance(url_raw, str) and not data.get("id"):
            data["id"] = article_id(canonical_url(url_raw))
        return data


class NewsSummary(BaseModel):
    """AI summary output per AI_BOUNDARIES §3.3 + operational fields for DB writeback."""

    news_id: int
    url: str
    summary: str = Field(min_length=1, max_length=600)
    affected_tickers: list[str] = Field(default_factory=list)
    sentiment_label: SentimentLabel
    caveats: list[str] = Field(default_factory=list)
    source_quality: SourceQuality
    confidence: float = Field(ge=0.0, le=1.0)
    not_financial_advice: Literal[True]
    prompt_template_id: str
    model: str
    summarized_at: datetime

    @field_validator("affected_tickers")
    @classmethod
    def _canon_tickers(cls, v: list[str]) -> list[str]:
        return [normalize_ticker(t) for t in v]

    @model_validator(mode="after")
    def _caveats_required_low_confidence(self) -> NewsSummary:
        if self.confidence < 0.7 and not self.caveats:
            raise ValueError("caveats must be non-empty when confidence < 0.7")
        return self


class FetchNewsResult(BaseModel):
    """Result wrapper per source per fetch. Adapter never raises; status carries failure."""

    source: str
    fetched_at: datetime
    status: FetchStatus
    articles: list[NewsArticle] = Field(default_factory=list)
    error_message: str | None = None
