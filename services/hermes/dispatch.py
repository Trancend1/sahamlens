"""Read-only tool dispatch: wire intent → core/agent tools + LLM calls (M4.4).

Each dispatch handler:
1. Calls the appropriate `core/agent` or `core/ai` function.
2. Captures `ai_log_id` linkage for LLM-backed calls.
3. Records one `agent_log` audit row.
4. Returns response text (policy-scanned upstream).
"""

from __future__ import annotations

import logging

import duckdb
from packages.core.agent.audit import AgentSurface, record_agent_interaction
from packages.core.agent.brief_delivery import format_brief_message
from packages.core.agent.tools import exposure_tool, journal_digest_tool
from packages.core.ai.generate_brief import generate_stock_brief
from packages.core.ai.provider import LLMProvider
from packages.core.ai.router import CircuitBreaker, ModelRouter
from packages.core.ai.stock_chat import answer_stock_question
from packages.core.alerts.repo import list_alert_events
from pydantic import BaseModel

from services.hermes.intents import Intent, ParsedIntent

logger = logging.getLogger(__name__)


class DispatchResult(BaseModel):
    """Result of dispatching an intent."""

    response_text: str
    agent_log_id: str | None = None
    requires_confirmation: bool = False
    confirmation_prompt: str = ""


def dispatch_intent(
    parsed: ParsedIntent,
    *,
    conn: duckdb.DuckDBPyConnection,
    provider: LLMProvider | None,
    router: ModelRouter,
    breaker: CircuitBreaker,
    session_id: str,
    surface: AgentSurface = "telegram",
) -> DispatchResult:
    """Route a parsed intent to its handler. Never raises — returns error text."""
    intent = parsed.intent

    if intent == Intent.BRIEF:
        return _handle_brief(parsed, conn, provider, router, breaker, session_id, surface)
    if intent == Intent.TICKER_SNAPSHOT:
        return _handle_ticker_snapshot(parsed, conn, provider, router, breaker, session_id, surface)
    if intent == Intent.EXPOSURE:
        return _handle_exposure(conn, session_id, surface)
    if intent == Intent.JOURNAL_DIGEST:
        return _handle_journal_digest(parsed, conn, session_id, surface)
    if intent == Intent.ALERT_TRIAGE:
        return _handle_alert_triage(parsed, conn, session_id, surface)
    if intent == Intent.HELP:
        return _handle_help(conn, session_id, surface)
    if intent == Intent.UNKNOWN:
        return _handle_unknown(parsed, conn, session_id, surface)

    return DispatchResult(response_text="Unknown intent. Type /help for commands.")


def _last_ai_log_id(conn: duckdb.DuckDBPyConnection) -> int | None:
    row = conn.execute("SELECT MAX(id) FROM ai_log").fetchone()
    if row and row[0] is not None:
        return int(row[0])
    return None


def _handle_brief(
    parsed: ParsedIntent,
    conn: duckdb.DuckDBPyConnection,
    provider: LLMProvider | None,
    router: ModelRouter,
    breaker: CircuitBreaker,
    session_id: str,
    surface: AgentSurface,
) -> DispatchResult:
    symbol = parsed.symbol or ""
    if not symbol:
        return DispatchResult(response_text="Please specify a ticker symbol. Example: /brief BBRI")
    if provider is None:
        return DispatchResult(
            response_text="LLM provider not configured. Set SAHAMLENS_LLM_PROVIDER and API key."
        )

    before = _last_ai_log_id(conn)
    brief = generate_stock_brief(
        symbol,
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
    )
    after = _last_ai_log_id(conn)
    ai_log_id = after if after is not None and after != before else None

    if brief is None:
        entry = record_agent_interaction(
            conn,
            session_id=session_id,
            surface=surface,
            intent="brief",
            command_text_redacted=f"symbol={symbol}",
            context_scope="ticker",
            ai_log_id=ai_log_id,
        )
        return DispatchResult(
            response_text=f"Could not generate brief for {symbol}. Budget may be exceeded or provider unavailable.",
            agent_log_id=entry.id,
        )

    text = format_brief_message(brief)
    entry = record_agent_interaction(
        conn,
        session_id=session_id,
        surface=surface,
        intent="brief",
        command_text_redacted=f"symbol={symbol}",
        context_scope="ticker",
        ai_log_id=ai_log_id,
    )
    return DispatchResult(response_text=text, agent_log_id=entry.id)


def _handle_ticker_snapshot(
    parsed: ParsedIntent,
    conn: duckdb.DuckDBPyConnection,
    provider: LLMProvider | None,
    router: ModelRouter,
    breaker: CircuitBreaker,
    session_id: str,
    surface: AgentSurface,
) -> DispatchResult:
    symbol = parsed.symbol or ""
    if not symbol:
        return DispatchResult(response_text="Please specify a ticker symbol. Example: /ticker BBRI")
    if provider is None:
        return DispatchResult(response_text="LLM provider not configured.")

    before = _last_ai_log_id(conn)
    response = answer_stock_question(
        question="Provide a quick snapshot of this ticker covering recent price action, key fundamentals, and notable news.",
        symbol=symbol,
        provider=provider,
        router=router,
        breaker=breaker,
        conn=conn,
    )
    after = _last_ai_log_id(conn)
    ai_log_id = after if after is not None and after != before else None

    if response is None:
        entry = record_agent_interaction(
            conn,
            session_id=session_id,
            surface=surface,
            intent="ticker_snapshot",
            command_text_redacted=f"symbol={symbol}",
            context_scope="ticker",
        )
        return DispatchResult(
            response_text=f"Could not fetch snapshot for {symbol}.",
            agent_log_id=entry.id,
        )

    text = _format_ticker_snapshot(response, symbol)
    entry = record_agent_interaction(
        conn,
        session_id=session_id,
        surface=surface,
        intent="ticker_snapshot",
        command_text_redacted=f"symbol={symbol}",
        context_scope="ticker",
        ai_log_id=ai_log_id,
    )
    return DispatchResult(response_text=text, agent_log_id=entry.id)


def _format_ticker_snapshot(response: object, symbol: str) -> str:
    from packages.core.ai.models import ChatResponse

    assert isinstance(response, ChatResponse)
    lines = [
        f"SahamLens snapshot — {symbol}",
        "",
        response.answer,
        "",
        "Evidence:",
    ]
    for item in response.evidence:
        lines.append(f"- [{item.type}] {item.value} (sumber: {item.source_ref})")
    if response.caveats:
        lines.append("")
        lines.append("Caveat:")
        lines.extend(f"- {c}" for c in response.caveats)
    lines.append("")
    lines.append("Bukan nasihat keuangan.")
    return "\n".join(lines)


def _handle_exposure(
    conn: duckdb.DuckDBPyConnection,
    session_id: str,
    surface: AgentSurface,
) -> DispatchResult:
    result = exposure_tool(conn, session_id=session_id, surface=surface)
    summary = result.summary
    lines = [
        "SahamLens portfolio exposure",
        f"Positions: {summary.position_count}",
        f"Top holding: {summary.top_concentration_pct:.1f}%",
        f"Top 3 concentration: {summary.top3_concentration_pct:.1f}%",
        "",
        "Holdings:",
    ]
    for h in summary.holdings:
        lines.append(f"- {h.symbol}: {h.weight_pct:.1f}%")
    lines.append("")
    lines.append("Bukan nasihat keuangan. Aggregate-only, tidak ada detail lot atau P&L.")
    return DispatchResult(response_text="\n".join(lines), agent_log_id=result.agent_log_id)


def _handle_journal_digest(
    parsed: ParsedIntent,
    conn: duckdb.DuckDBPyConnection,
    session_id: str,
    surface: AgentSurface,
) -> DispatchResult:
    result = journal_digest_tool(conn, session_id=session_id, surface=surface, symbol=parsed.symbol)
    digest = result.digest
    if digest.entry_count == 0:
        suffix = f" for {parsed.symbol}" if parsed.symbol else ""
        return DispatchResult(
            response_text=f"No journal entries found.{suffix}",
            agent_log_id=result.agent_log_id,
        )
    lines = [
        "SahamLens journal digest",
        f"Entries: {digest.entry_count}",
        "",
    ]
    if digest.by_status:
        lines.append("By status:")
        lines.extend(f"- {k}: {v}" for k, v in sorted(digest.by_status.items()))
    if digest.by_setup:
        lines.append("By setup:")
        lines.extend(f"- {k}: {v}" for k, v in sorted(digest.by_setup.items()))
    if digest.by_emotion:
        lines.append("By emotion:")
        lines.extend(f"- {k}: {v}" for k, v in sorted(digest.by_emotion.items()))
    if digest.missing_invalidation_count:
        lines.append(f"Missing invalidation: {digest.missing_invalidation_count}")
    if digest.missing_emotion_count:
        lines.append(f"Missing emotion: {digest.missing_emotion_count}")
    lines.append("")
    lines.append("Redacted digest. Trade thesis and rupiah amounts are excluded.")
    return DispatchResult(response_text="\n".join(lines), agent_log_id=result.agent_log_id)


def _handle_alert_triage(
    parsed: ParsedIntent,
    conn: duckdb.DuckDBPyConnection,
    session_id: str,
    surface: AgentSurface,
) -> DispatchResult:
    action = parsed.alert_action or ""
    if action in ("list", ""):
        events = list_alert_events(conn, limit=10)
        if not events:
            return DispatchResult(
                response_text="No alert events found.",
            )
        lines = ["Active alert events (last 10):", ""]
        for ev in events:
            lines.append(f"- [{ev.status}] {ev.ticker}: {ev.title} ({ev.created_at.date()})")
        entry = record_agent_interaction(
            conn,
            session_id=session_id,
            surface=surface,
            intent="alert_triage",
            command_text_redacted="action=list",
            context_scope="alert",
        )
        return DispatchResult(
            response_text="\n".join(lines),
            agent_log_id=entry.id,
        )

    entry = record_agent_interaction(
        conn,
        session_id=session_id,
        surface=surface,
        intent="alert_triage",
        command_text_redacted=f"action={action}",
        context_scope="alert",
    )
    return DispatchResult(
        response_text=(
            f"Action '{action}' requires confirmation. "
            f"Reply with 'yes' to confirm {action} for this alert."
        ),
        agent_log_id=entry.id,
        requires_confirmation=True,
        confirmation_prompt=f"confirm alert {action} {parsed.alert_event_id or ''}",
    )


def _handle_help(
    conn: duckdb.DuckDBPyConnection,
    session_id: str,
    surface: AgentSurface,
) -> DispatchResult:
    entry = record_agent_interaction(
        conn,
        session_id=session_id,
        surface=surface,
        intent="help",
        command_text_redacted="/help",
        context_scope="none",
    )
    text = "\n".join(
        [
            "SahamLens Hermes — tersedia perintah:",
            "",
            "/brief <ticker>      — analisis mendalam saham",
            "/ticker <ticker>     — snapshot cepat saham",
            "/exposure            — ringkasan portofolio",
            "/digest [ticker]     — ringkasan jurnal",
            "/alert list          — daftar alert",
            "/alert ack <id>      — konfirmasi alert",
            "/alert fp <id>       — tandai false positive",
            "/journal <text>      — catat jurnal",
            "/research <tkr> <note> — tambah riset",
            "/help                — tampilkan ini",
            "",
            "Bukan nasihat keuangan. Selalu verifikasi data sendiri.",
        ]
    )
    return DispatchResult(response_text=text, agent_log_id=entry.id)


def _handle_unknown(
    parsed: ParsedIntent,
    conn: duckdb.DuckDBPyConnection,
    session_id: str,
    surface: AgentSurface,
) -> DispatchResult:
    entry = record_agent_interaction(
        conn,
        session_id=session_id,
        surface=surface,
        intent="unknown",
        command_text_redacted=parsed.raw_text[:80],
        context_scope="none",
    )
    return DispatchResult(
        response_text=(
            f'Maaf, saya tidak mengerti "{parsed.raw_text[:60]}". '
            "Ketik /help untuk melihat perintah yang tersedia."
        ),
        agent_log_id=entry.id,
    )
