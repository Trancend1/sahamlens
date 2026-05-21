"""Trade plan → JournalCritique orchestrator.

Pipeline: budget check → prompt render → provider call → schema validate → log → return.
No retry (critique is advisory; one attempt is sufficient for MVP).
"""

from __future__ import annotations

import json
import logging

import duckdb
from packages.core.ai.prompts import PromptTemplate, load_template
from packages.core.ai.provider import LLMProvider
from packages.core.ai.router import BudgetExceeded, CircuitBreaker, ModelRouter
from packages.core.journal.models import JournalCritique, TradePlan
from packages.core.news.repo import log_ai_call
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


def critique_trade_plan(
    plan: TradePlan,
    *,
    provider: LLMProvider,
    router: ModelRouter,
    breaker: CircuitBreaker,
    conn: duckdb.DuckDBPyConnection,
    template: PromptTemplate | None = None,
) -> JournalCritique | None:
    """Generate a structured critique for a trade plan.

    Returns None on budget exceeded, provider error, or schema validation failure.
    """
    tpl = template or load_template("journal_critique", version=1)
    model = router.select("journal_critique")

    try:
        breaker.check(conn, model)
    except BudgetExceeded as exc:
        logger.warning("budget exceeded for plan %s: %s", plan.id, exc)
        return None

    user_msg = tpl.render_user(
        plan_id=plan.id,
        symbol=plan.symbol,
        setup_type=plan.setup_type,
        thesis=plan.thesis,
        entry_plan=plan.entry_plan,
        stop_level=plan.stop_level,
        invalidation=plan.invalidation,
        target=plan.target,
        position_size_rupiah=plan.position_size_rupiah,
        max_loss_rupiah=plan.max_loss_rupiah,
        emotion=plan.emotion or "tidak disebutkan",
    )
    input_context = json.dumps({"plan_id": plan.id, "symbol": plan.symbol}, ensure_ascii=False)

    raw_output = provider.complete_json(
        system=tpl.system,
        user=user_msg,
        schema=_schema_for_provider(plan.id),
        schema_name="journal_critique",
        model=model,
    )

    if raw_output is None:
        logger.warning("provider returned None for plan %s", plan.id)
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

    try:
        critique = JournalCritique.model_validate(raw_output)
    except PydanticValidationError as exc:
        logger.warning("schema validation failed for plan %s: %s", plan.id, exc)
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

    log_ai_call(
        conn,
        prompt_template_id=tpl.template_id,
        model=model,
        input_context=input_context,
        output=json.dumps(raw_output, ensure_ascii=False),
        confidence=None,
        caveats_count=len(critique.caveats),
    )
    return critique


def _schema_for_provider(plan_id: int) -> dict[str, object]:
    """JSON Schema for journal_critique tool_use input. Mirrors AI_BOUNDARIES §3.2."""
    return {
        "type": "object",
        "properties": {
            "plan_id": {"type": "integer"},
            "checks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": [
                                "thesis",
                                "invalidation",
                                "risk",
                                "catalyst",
                                "emotion",
                                "liquidity",
                            ],
                        },
                        "status": {"type": "string", "enum": ["ok", "weak", "missing"]},
                        "finding": {"type": "string"},
                        "suggested_question": {"type": "string"},
                    },
                    "required": ["category", "status", "finding", "suggested_question"],
                },
            },
            "overall_risk_flag": {
                "type": "string",
                "enum": ["green", "amber", "red", "incomplete"],
            },
            "caveats": {"type": "array", "items": {"type": "string"}},
            "not_financial_advice": {"type": "boolean"},
        },
        "required": [
            "plan_id",
            "checks",
            "overall_risk_flag",
            "caveats",
            "not_financial_advice",
        ],
    }
