"""Stock chat Q&A with RAG context.

Single-turn question answering scoped to one stock. Client passes optional
prior turns (formatted string) for context continuity within the same session.
Pipeline: budget check → context build → prompt render → provider call → validate → log → return.
No retry — advisory response, one attempt per question.
"""

from __future__ import annotations

import json
import logging

import duckdb
from packages.core.ai.context_builder import build_stock_context
from packages.core.ai.models import ChatResponse
from packages.core.ai.prompts import PromptTemplate, load_template
from packages.core.ai.provider import LLMProvider
from packages.core.ai.router import BudgetExceeded, CircuitBreaker, ModelRouter
from packages.core.ai.validator import ValidationError, validate_chat_response
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.news.repo import log_ai_call
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


def answer_stock_question(
    question: str,
    symbol: str,
    *,
    provider: LLMProvider,
    router: ModelRouter,
    breaker: CircuitBreaker,
    conn: duckdb.DuckDBPyConnection,
    prior_turns: str = "",
    template: PromptTemplate | None = None,
) -> ChatResponse | None:
    """Answer a contextual question about a stock using local RAG context.

    Returns None on budget exceeded, provider error, or schema validation failure.
    """
    canonical = normalize_ticker(symbol)
    tpl = template or load_template("stock_chat", version=1)
    model = router.select("stock_chat")

    try:
        breaker.check(conn, model)
    except BudgetExceeded as exc:
        logger.warning("budget exceeded for chat %s: %s", canonical, exc)
        return None

    ctx = build_stock_context(conn, canonical)
    user_msg = tpl.render_user(
        symbol=canonical,
        context_text=ctx.as_text(),
        prior_turns=prior_turns or "(tidak ada riwayat sebelumnya)",
        question=question,
    )
    input_context = json.dumps(
        {"symbol": canonical, "question": question[:200]}, ensure_ascii=False
    )

    raw_output = provider.complete_json(
        system=tpl.system,
        user=user_msg,
        schema=_schema_for_provider(),
        schema_name="chat_response",
        model=model,
        max_tokens=800,
    )

    if raw_output is None:
        logger.warning("provider returned None for chat %s", canonical)
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

    payload: dict[str, object] = {
        **raw_output,
        "question": question,
        "not_financial_advice": True,
    }

    try:
        response = validate_chat_response(payload, ChatResponse)
    except (ValidationError, PydanticValidationError) as exc:
        logger.warning("chat response validation failed for %s: %s", canonical, exc)
        log_ai_call(
            conn,
            prompt_template_id=tpl.template_id,
            model=model,
            input_context=input_context,
            output=json.dumps(raw_output, ensure_ascii=False),
            confidence=None,
            caveats_count=0,
        )
        return None

    assert isinstance(response, ChatResponse)
    log_ai_call(
        conn,
        prompt_template_id=tpl.template_id,
        model=model,
        input_context=input_context,
        output=json.dumps(raw_output, ensure_ascii=False),
        confidence=None,
        caveats_count=len(response.caveats),
    )
    return response


def _schema_for_provider() -> dict[str, object]:
    """JSON Schema for chat_response tool_use input."""
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
            "answer": {"type": "string"},
            "evidence": {"type": "array", "items": evidence_item},
            "caveats": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["answer", "evidence", "caveats"],
    }
