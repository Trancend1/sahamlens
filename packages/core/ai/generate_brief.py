"""Stock brief generator — analysis_output schema (AI_BOUNDARIES.md §3.1).

Pipeline: budget check → context build → prompt render → provider call
         → validate → log → return StockBrief | None.
Retries up to 3x on banned-phrase violation (same as summarize_news).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

import duckdb
from packages.core.ai.context_builder import build_stock_context
from packages.core.ai.models import StockBrief
from packages.core.ai.prompts import PromptTemplate, load_template
from packages.core.ai.provider import LLMProvider
from packages.core.ai.router import BudgetExceeded, CircuitBreaker, ModelRouter
from packages.core.ai.validator import ValidationError, validate_stock_brief
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.news.repo import log_ai_call

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


def generate_stock_brief(
    symbol: str,
    *,
    provider: LLMProvider,
    router: ModelRouter,
    breaker: CircuitBreaker,
    conn: duckdb.DuckDBPyConnection,
    template: PromptTemplate | None = None,
    now: datetime | None = None,
) -> StockBrief | None:
    """Generate structured stock analysis brief.

    Returns None on budget exceeded, provider error, or validation failure after retries.
    """
    canonical = normalize_ticker(symbol)
    tpl = template or load_template("stock_brief", version=1)
    model = router.select("daily_brief")
    now_ts = now or datetime.now(UTC)

    try:
        breaker.check(conn, model)
    except BudgetExceeded as exc:
        logger.warning("budget exceeded for brief %s: %s", canonical, exc)
        return None

    ctx = build_stock_context(conn, canonical)
    user_msg = tpl.render_user(
        symbol=canonical,
        analysis_date=now_ts.date().isoformat(),
        context_text=ctx.as_text(),
    )
    input_context = json.dumps({"symbol": canonical, "analysis_date": now_ts.date().isoformat()})

    schema = _schema_for_provider()
    last_error = "no attempts"

    for attempt in range(1, MAX_RETRIES + 1):
        raw_output = provider.complete_json(
            system=tpl.system,
            user=user_msg,
            schema=schema,
            schema_name="stock_brief",
            model=model,
            max_tokens=1500,
        )

        if raw_output is None:
            logger.warning("provider returned None for brief %s", canonical)
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

        payload = _hydrate_payload(raw_output, canonical, tpl, model, now_ts)
        try:
            brief = validate_stock_brief(payload, StockBrief)
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

        assert isinstance(brief, StockBrief)
        log_ai_call(
            conn,
            prompt_template_id=tpl.template_id,
            model=model,
            input_context=input_context,
            output=json.dumps(raw_output, ensure_ascii=False),
            confidence=None,
            caveats_count=len(brief.caveats),
        )
        return brief

    logger.warning("generate_brief exhausted retries for %s: %s", canonical, last_error)
    return None


def _hydrate_payload(
    raw: dict[str, object],
    symbol: str,
    tpl: PromptTemplate,
    model: str,
    now_ts: datetime,
) -> dict[str, object]:
    return {
        **raw,
        "symbol": symbol,
        "analysis_date": now_ts.date().isoformat(),
        "prompt_template_id": tpl.template_id,
        "model": model,
        "not_financial_advice": True,
    }


def _schema_for_provider() -> dict[str, object]:
    """JSON Schema for stock_brief tool_use input. Mirrors AI_BOUNDARIES.md §3.1."""
    evidence_item = {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["price", "indicator", "news", "fundamental", "journal"],
            },
            "value": {"type": "string"},
            "source_ref": {"type": "string"},
            "freshness": {"type": "string"},
        },
        "required": ["type", "value", "source_ref", "freshness"],
    }
    return {
        "type": "object",
        "properties": {
            "evidence": {"type": "array", "items": evidence_item},
            "bullish_view": {"type": "string"},
            "bearish_view": {"type": "string"},
            "uncertainty": {"type": "string"},
            "caveats": {"type": "array", "items": {"type": "string"}},
            "beginner_explanation": {"type": "string"},
            "suggested_next_question": {"type": "string"},
        },
        "required": [
            "evidence",
            "bullish_view",
            "bearish_view",
            "uncertainty",
            "caveats",
            "beginner_explanation",
            "suggested_next_question",
        ],
    }
