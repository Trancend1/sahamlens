"""Tests for intent dispatch: routing, auditing, LLM/non-LLM paths."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
from packages.core.ai.provider import (
    AnthropicProvider,
)
from packages.core.ai.router import CircuitBreaker, CostBudget, ModelRouter
from packages.core.journal.models import TradePlan
from packages.core.journal.repo import create_plan
from packages.core.portfolio.models import PortfolioPosition
from packages.core.portfolio.repo import replace_positions
from scripts.migrate import applied_versions, apply_migration, discover_migrations

from services.hermes.dispatch import dispatch_intent
from services.hermes.intents import parse_intent


def _migrated_db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
    return conn


def _router() -> ModelRouter:
    return ModelRouter()


def _breaker() -> CircuitBreaker:
    return CircuitBreaker(CostBudget(daily_usd_cap=999.0))


def _fake_anthropic(json_payload: object) -> AnthropicProvider:
    def fake_post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
        return json.dumps(
            {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "stock_brief",
                        "input": {
                            "evidence": [
                                {
                                    "type": "price",
                                    "value": "Price moved 2%",
                                    "source_ref": "test",
                                    "freshness": "2026-06-15",
                                }
                            ],
                            "bullish_view": "Stable trend",
                            "bearish_view": "Volume declining",
                            "uncertainty": "Earnings next week",
                            "caveats": ["Not financial advice"],
                            "beginner_explanation": "Simple view",
                            "suggested_next_question": "Check PE ratio",
                        },
                    }
                ],
            }
        ).encode("utf-8")

    return AnthropicProvider(api_key="sk-test", post=fake_post)  # pragma: allowlist secret


# --- Non-LLM dispatch tests ---


def test_dispatch_help(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        parsed = parse_intent("/help")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=None,
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert result.response_text.startswith("SahamLens Hermes")
    assert "/brief" in result.response_text


def test_dispatch_unknown(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        parsed = parse_intent("some random text")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=None,
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert "tidak mengerti" in result.response_text


def test_dispatch_exposure_without_data(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        parsed = parse_intent("/exposure")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=None,
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert "portfolio exposure" in result.response_text.lower()
    assert result.agent_log_id is not None
    assert result.agent_log_id.startswith("agent-log-")


def test_dispatch_exposure_with_holdings(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        replace_positions(
            conn,
            [
                PortfolioPosition(
                    symbol="BBCA",
                    lots=100,
                    avg_price=5000.0,
                    imported_at=datetime.now(UTC),
                    source="csv",
                ),
                PortfolioPosition(
                    symbol="BBRI",
                    lots=200,
                    avg_price=4000.0,
                    imported_at=datetime.now(UTC),
                    source="csv",
                ),
            ],
        )
        parsed = parse_intent("/exposure")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=None,
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert "BBCA" in result.response_text
    assert "BBRI" in result.response_text


def test_dispatch_journal_digest_empty(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        parsed = parse_intent("/digest")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=None,
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert "No journal entries" in result.response_text


def test_dispatch_journal_digest_with_data(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        create_plan(
            conn,
            TradePlan(
                id=1,
                symbol="BBCA",
                setup_type="breakout",
                thesis="Growth thesis",
                entry_plan="Limit entry",
                stop_level=9000.0,
                invalidation="below support",
                target="Hold long term",
                position_size_rupiah=50000000,
                max_loss_rupiah=10000000,
                emotion="calm",
                created_at=datetime.now(UTC),
            ),
        )
        parsed = parse_intent("/digest BBCA")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=None,
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert "BBCA" in result.response_text or "journal" in result.response_text.lower()
    assert result.agent_log_id is not None


def test_dispatch_alert_list(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        parsed = parse_intent("/alert list")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=None,
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert result.response_text is not None


def test_dispatch_brief_without_provider(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        parsed = parse_intent("/brief BBRI")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=None,
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert "not configured" in result.response_text.lower()


def test_dispatch_brief_without_symbol(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        parsed = parse_intent("/brief")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=_fake_anthropic({}),
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert "specify a ticker" in result.response_text.lower()


def test_dispatch_brief_with_fake_provider(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        parsed = parse_intent("/brief BBRI")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=_fake_anthropic({}),
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert result.agent_log_id is not None
    assert "SahamLens brief" in result.response_text


def test_dispatch_ticker_without_provider(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        parsed = parse_intent("/ticker BBRI")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=None,
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert "not configured" in result.response_text.lower()


def test_dispatch_ticker_without_symbol(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        parsed = parse_intent("/ticker")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=_fake_anthropic({}),
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert "specify a ticker" in result.response_text.lower()


def test_dispatch_alert_write_action_needs_confirmation(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        parsed = parse_intent("/alert ack evt-123")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=None,
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
    assert result.requires_confirmation is True
    assert "confirmation" in result.response_text.lower()


def test_ai_log_id_linked_on_brief(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    try:
        parsed = parse_intent("/brief BBRI")
        result = dispatch_intent(
            parsed,
            conn=conn,
            provider=_fake_anthropic({}),
            router=_router(),
            breaker=_breaker(),
            session_id="sess-1",
        )
        assert result.agent_log_id is not None
        row = conn.execute(
            "SELECT ai_log_id FROM agent_log WHERE id = ?",
            [result.agent_log_id],
        ).fetchone()
        fetched = conn.execute("SELECT id FROM ai_log ORDER BY id DESC LIMIT 1").fetchone()
        if fetched:
            assert row is not None and row[0] == fetched[0]
    finally:
        conn.close()
