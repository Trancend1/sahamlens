"""Non-advisory policy gate (ADR-0018, M4.3).

Two responsibilities:
1. Intent-level check — reject forbidden intents (buy/sell/target/auto-exec).
2. Outbound-text check — run `scan_banned` before any chat-surface send.

Read-only is the default. Write intents require explicit confirmation.
"""

from __future__ import annotations

from packages.core.ai.validator import scan_banned
from pydantic import BaseModel

from services.hermes.intents import Intent

# Intents that modify local data. Require explicit confirmation.
WRITE_INTENTS: frozenset[Intent] = frozenset(
    {
        Intent.ALERT_TRIAGE,
        Intent.JOURNAL_CAPTURE,
        Intent.RESEARCH_ADD,
    }
)

# Intents that are inherently forbidden (non-existent in current Intent enum,
# but listed here for future-proofing and defense-in-depth).
FORBIDDEN_INTENTS: frozenset[Intent] = frozenset()


class PolicyDecision(BaseModel):
    """Result of a policy check."""

    allowed: bool
    reason: str = ""
    banned_hit: str | None = None
    requires_confirmation: bool = False


def check_intent_allowed(intent: Intent) -> PolicyDecision:
    """Reject forbidden intents. Read-only by default."""
    if intent in FORBIDDEN_INTENTS:
        return PolicyDecision(
            allowed=False,
            reason=(
                "I cannot provide buy, sell, or target price advice. "
                "SahamLens is a research tool, not a trading advisor."
            ),
        )
    return PolicyDecision(
        allowed=True,
        requires_confirmation=intent in WRITE_INTENTS,
    )


def check_outbound_text(text: str) -> PolicyDecision:
    """Run scan_banned on outgoing text. Reject if any banned pattern matches."""
    hit = scan_banned(text)
    if hit is not None:
        return PolicyDecision(
            allowed=False,
            banned_hit=str(hit),
            reason="Response contains a banned phrase and cannot be sent.",
        )
    return PolicyDecision(allowed=True)


def require_confirmation(intent: Intent) -> bool:
    """Return True when an intent needs explicit user confirmation."""
    return intent in WRITE_INTENTS
