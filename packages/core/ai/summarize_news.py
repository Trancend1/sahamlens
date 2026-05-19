"""Article → NewsSummary orchestrator.

Pipeline: budget check → prompt render → provider call → validator → log → return.
Banned-phrase rejection triggers up to 3 retries (per AI_BOUNDARIES §4.4). Hard fail
after retries returns None — caller skips article + ai_log records the attempt.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime

import duckdb
from packages.core.ai.prompts import PromptTemplate, load_template
from packages.core.ai.provider import LLMProvider
from packages.core.ai.router import BudgetExceeded, CircuitBreaker, ModelRouter
from packages.core.ai.validator import ValidationError, validate_news_summary
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.news.models import NewsArticle, NewsSummary
from packages.core.news.repo import log_ai_call
from packages.core.news.rss_source import SOURCE_QUALITY

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
LOW_CONFIDENCE_NO_TICKER_PENALTY = 0.1
STALE_AGE_DAYS = 7
STALE_AGE_PENALTY = 0.05


def detect_affected_tickers(text: str, watchlist: list[str]) -> list[str]:
    """Regex match watchlist tickers in `text`. Accepts bare code or `.JK` form."""
    found: list[str] = []
    seen: set[str] = set()
    for ticker in watchlist:
        try:
            canonical = normalize_ticker(ticker)
        except ValueError:
            continue
        bare = canonical.removesuffix(".JK")
        pattern = re.compile(rf"\b{re.escape(bare)}(\.JK)?\b", re.IGNORECASE)
        if pattern.search(text) and canonical not in seen:
            seen.add(canonical)
            found.append(canonical)
    return found


def adjust_confidence(raw: float, *, has_tickers: bool, age_days: int) -> float:
    score = raw
    if not has_tickers:
        score -= LOW_CONFIDENCE_NO_TICKER_PENALTY
    if age_days > STALE_AGE_DAYS:
        score -= STALE_AGE_PENALTY
    return max(0.0, min(1.0, score))


def summarize_news(
    article: NewsArticle,
    *,
    watchlist: list[str],
    provider: LLMProvider,
    router: ModelRouter,
    breaker: CircuitBreaker,
    conn: duckdb.DuckDBPyConnection,
    template: PromptTemplate | None = None,
    now: datetime | None = None,
) -> NewsSummary | None:
    tpl = template or load_template("news_summary", version=1)
    model = router.select("news_summary")
    try:
        breaker.check(conn, model)
    except BudgetExceeded as exc:
        logger.warning("budget exceeded for %s: %s", article.id, exc)
        return None

    user_msg = tpl.render_user(
        title=article.title,
        source=article.source,
        published_at=article.published_at.isoformat(),
        url=article.url,
        raw_summary=article.raw_summary or "(tidak tersedia)",
        watchlist_tickers=", ".join(watchlist) if watchlist else "(kosong)",
        news_id=article.id,
    )
    input_context = json.dumps(
        {"article_id": article.id, "watchlist_count": len(watchlist)}, ensure_ascii=False
    )

    schema = _schema_for_provider()
    last_error: str = "no attempts"
    for attempt in range(1, MAX_RETRIES + 1):
        raw_output = provider.complete_json(
            system=tpl.system,
            user=user_msg,
            schema=schema,
            schema_name="news_summary",
            model=model,
        )
        if raw_output is None:
            last_error = "provider returned None"
            log_ai_call(
                conn,
                prompt_template_id=tpl.template_id,
                model=model,
                input_context=input_context,
                output="",
                confidence=None,
                caveats_count=0,
            )
            return None

        payload = _hydrate_payload(article, raw_output, watchlist, tpl, model, now=now)
        try:
            parsed = validate_news_summary(payload, NewsSummary)
        except ValidationError as exc:
            last_error = f"{exc.reason}: {exc.detail}"
            log_ai_call(
                conn,
                prompt_template_id=tpl.template_id,
                model=model,
                input_context=input_context,
                output=json.dumps(raw_output, ensure_ascii=False),
                confidence=None,
                caveats_count=0,
            )
            if exc.reason != "banned_phrase" or attempt == MAX_RETRIES:
                logger.warning("validation failed (attempt %d): %s", attempt, exc)
                return None
            continue

        assert isinstance(parsed, NewsSummary)
        log_ai_call(
            conn,
            prompt_template_id=tpl.template_id,
            model=model,
            input_context=input_context,
            output=json.dumps(raw_output, ensure_ascii=False),
            confidence=parsed.confidence,
            caveats_count=len(parsed.caveats),
        )
        return parsed

    logger.warning("summarize_news exhausted retries for %s: %s", article.id, last_error)
    return None


def _schema_for_provider() -> dict[str, object]:
    """JSON Schema for the news_summary tool_use input. Mirrors AI_BOUNDARIES §3.3."""
    return {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "maxLength": 600},
            "affected_tickers": {"type": "array", "items": {"type": "string"}},
            "sentiment_label": {
                "type": "string",
                "enum": ["bullish", "neutral", "bearish", "mixed"],
            },
            "caveats": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
        "required": ["summary", "sentiment_label", "confidence"],
    }


def _hydrate_payload(
    article: NewsArticle,
    raw: dict[str, object],
    watchlist: list[str],
    tpl: PromptTemplate,
    model: str,
    *,
    now: datetime | None,
) -> dict[str, object]:
    """Combine LLM output with operational fields + intersection ticker logic."""
    now_ts = now or datetime.now(UTC)

    text_for_match = " ".join(
        [
            article.title,
            article.raw_summary or "",
            str(raw.get("summary", "")),
        ]
    )
    regex_tickers = detect_affected_tickers(text_for_match, watchlist)
    llm_tickers_raw = raw.get("affected_tickers")
    llm_tickers: list[str] = []
    if isinstance(llm_tickers_raw, list):
        for item in llm_tickers_raw:
            if not isinstance(item, str):
                continue
            try:
                llm_tickers.append(normalize_ticker(item))
            except ValueError:
                continue

    if llm_tickers and regex_tickers:
        intersected = [t for t in llm_tickers if t in regex_tickers]
    else:
        intersected = llm_tickers or regex_tickers

    conf_raw = raw.get("confidence", 0.0)
    raw_conf = float(conf_raw) if isinstance(conf_raw, int | float) else 0.0
    age_days = max(0, (now_ts - article.published_at).days)
    adjusted_conf = adjust_confidence(raw_conf, has_tickers=bool(intersected), age_days=age_days)

    caveats_raw = raw.get("caveats")
    caveats = [str(c) for c in caveats_raw] if isinstance(caveats_raw, list) else []
    if adjusted_conf < 0.7 and not caveats:
        caveats = ["Confidence rendah — verifikasi manual."]

    return {
        "news_id": article.id,
        "url": article.url,
        "summary": str(raw.get("summary", "")).strip(),
        "affected_tickers": intersected,
        "sentiment_label": raw.get("sentiment_label", "neutral"),
        "caveats": caveats,
        "source_quality": SOURCE_QUALITY.get(article.source.lower(), "unknown"),
        "confidence": adjusted_conf,
        "not_financial_advice": True,
        "prompt_template_id": tpl.template_id,
        "model": model,
        "summarized_at": now_ts,
    }
