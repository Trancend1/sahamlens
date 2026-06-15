"""Redacted journal digest for the agentic layer (ADR-0019 D5).

Hard privacy boundary: free-text fields (thesis, entry_plan, invalidation,
target, lesson) and rupiah amounts (position size, max loss, result) MUST NOT
appear in the output. Only structural counts are exposed, so the digest is safe
to send to an LLM or chat surface without explicit raw-text opt-in.
"""

from __future__ import annotations

from collections import Counter

import duckdb
from packages.core.journal.repo import list_plans
from pydantic import BaseModel

REDACTED_DIGEST_NOTE = (
    "Redacted digest only. Trade thesis, plan free-text, and rupiah amounts are "
    "intentionally excluded. Raw journal text requires explicit opt-in."
)


class JournalDigest(BaseModel):
    """Structural counts over trade plans, with no free-text or rupiah detail."""

    entry_count: int
    by_status: dict[str, int]
    by_setup: dict[str, int]
    by_emotion: dict[str, int]
    missing_invalidation_count: int
    missing_emotion_count: int
    note: str = REDACTED_DIGEST_NOTE
    not_financial_advice: bool = True


def journal_digest(
    conn: duckdb.DuckDBPyConnection,
    *,
    symbol: str | None = None,
) -> JournalDigest:
    """Return a redacted digest. Reads `journal`, writes nothing.

    `symbol` optionally scopes the digest to one ticker (per-command opt-in).
    """
    plans = list_plans(conn, symbol=symbol)
    return JournalDigest(
        entry_count=len(plans),
        by_status=dict(Counter(p.status for p in plans)),
        by_setup=dict(Counter(p.setup_type for p in plans)),
        by_emotion=dict(Counter(p.emotion or "unspecified" for p in plans)),
        missing_invalidation_count=sum(1 for p in plans if not p.invalidation.strip()),
        missing_emotion_count=sum(1 for p in plans if p.emotion is None),
    )
