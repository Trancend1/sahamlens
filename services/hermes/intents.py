"""Intent router: parse command/text → typed Intent (M4.2).

Supports both slash commands (/brief BBRI) and natural language ("brief on BBRI").
Unknown input returns a safe fallback.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel


class Intent(StrEnum):
    BRIEF = "brief"
    TICKER_SNAPSHOT = "ticker_snapshot"
    ALERT_TRIAGE = "alert_triage"
    JOURNAL_CAPTURE = "journal_capture"
    RESEARCH_ADD = "research_add"
    EXPOSURE = "exposure"
    JOURNAL_DIGEST = "journal_digest"
    HELP = "help"
    UNKNOWN = "unknown"


class ParsedIntent(BaseModel):
    intent: Intent
    raw_text: str
    symbol: str | None = None
    alert_action: str | None = None
    alert_event_id: str | None = None
    journal_text: str | None = None
    research_symbol: str | None = None
    research_note: str | None = None


def parse_intent(text: str) -> ParsedIntent:
    """Parse raw user text into a typed intent with extracted arguments."""
    raw = text.strip()
    if not raw:
        return ParsedIntent(intent=Intent.UNKNOWN, raw_text=text)

    result = _try_slash_command(raw)
    if result is not None:
        return result

    result = _try_natural_language(raw)
    if result is not None:
        return result

    return ParsedIntent(intent=Intent.UNKNOWN, raw_text=text)


def _try_slash_command(text: str) -> ParsedIntent | None:
    """Match /command <args> patterns. Returns None on no match."""
    lowered = text.lower().strip()

    # /brief|brf [symbol]
    m = re.match(r"^/(?:brief|brf)(?:\s+([a-z]{2,4}))?\s*$", lowered)
    if m:
        return ParsedIntent(
            intent=Intent.BRIEF,
            raw_text=text,
            symbol=m.group(1).upper() if m.group(1) else None,
        )

    # /ticker|tck|t [symbol]
    m = re.match(r"^/(?:ticker|tck|t)(?:\s+([a-z]{2,4}))?\s*$", lowered)
    if m:
        return ParsedIntent(
            intent=Intent.TICKER_SNAPSHOT,
            raw_text=text,
            symbol=m.group(1).upper() if m.group(1) else None,
        )

    # /alert|al <action> [event_id]
    m = re.match(r"^/(?:alert|al)\s+(\S+)(?:\s+(\S+))?", lowered)
    if m:
        action = m.group(1)
        event_id = m.group(2)
        return ParsedIntent(
            intent=Intent.ALERT_TRIAGE,
            raw_text=text,
            alert_action=action,
            alert_event_id=event_id,
        )

    # /journal|jrn <text...>
    m = re.match(r"^/(?:journal|jrn)\s+(.+)", text)
    if m:
        return ParsedIntent(
            intent=Intent.JOURNAL_CAPTURE,
            raw_text=text,
            journal_text=m.group(1).strip(),
        )

    # /research|res <symbol> <note...>
    m = re.match(r"^/(?:research|res)\s+([a-z]{2,4})\s+(.+)", lowered)
    if m:
        return ParsedIntent(
            intent=Intent.RESEARCH_ADD,
            raw_text=text,
            research_symbol=m.group(1).upper(),
            research_note=m.group(2).strip(),
        )

    # /exposure|exp|port
    if re.match(r"^/(?:exposure|exp|port)$", lowered):
        return ParsedIntent(intent=Intent.EXPOSURE, raw_text=text)

    # /digest|dg [symbol]
    m = re.match(r"^/(?:digest|dg)\s*([a-z]{2,4})?\s*$", lowered)
    if m:
        return ParsedIntent(
            intent=Intent.JOURNAL_DIGEST,
            raw_text=text,
            symbol=m.group(1).upper() if m.group(1) else None,
        )

    # /help|h
    if re.match(r"^/(?:help|h)\s*$", lowered):
        return ParsedIntent(intent=Intent.HELP, raw_text=text)

    return None


def _try_natural_language(text: str) -> ParsedIntent | None:
    """Match natural language patterns. Returns None on no match."""
    lowered = text.lower().strip()

    # "brief on <symbol>", "brief <symbol>"
    m = re.match(r"^(?:brief|brie?f)\s+(?:on\s+)?([a-z]{2,4})$", lowered)
    if m:
        return ParsedIntent(
            intent=Intent.BRIEF,
            raw_text=text,
            symbol=m.group(1).upper(),
        )

    # "snapshot of <symbol>", "ticker <symbol>"
    m = re.match(r"^(?:(?:snapshot|info)\s+(?:of\s+)?|ticker\s+)([a-z]{2,4})$", lowered)
    if m:
        return ParsedIntent(
            intent=Intent.TICKER_SNAPSHOT,
            raw_text=text,
            symbol=m.group(1).upper(),
        )

    # "exposure", "portfolio", "my portfolio"
    if re.match(r"^(?:exposure|port(?:folio)?|my\s+port(?:folio)?)$", lowered):
        return ParsedIntent(intent=Intent.EXPOSURE, raw_text=text)

    # "digest", "journal summary", "digest <symbol>"
    m = re.match(r"^digest\s*([a-z]{2,4})?$|^journal\s+(?:summary|digest)\s*$", lowered)
    if m:
        return ParsedIntent(
            intent=Intent.JOURNAL_DIGEST,
            raw_text=text,
            symbol=m.group(1).upper() if m.group(1) else None,
        )

    # "help"
    if re.match(r"^help\s*$|^\?\s*$", lowered):
        return ParsedIntent(intent=Intent.HELP, raw_text=text)

    return None
