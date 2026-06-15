"""Tests for intent router: slash commands, natural language, unknown fallback."""

from __future__ import annotations

from services.hermes.intents import Intent, ParsedIntent, parse_intent


def _assert_brief(result: ParsedIntent, symbol: str) -> None:
    assert result.intent == Intent.BRIEF
    assert result.symbol == symbol


def _assert_ticker(result: ParsedIntent, symbol: str) -> None:
    assert result.intent == Intent.TICKER_SNAPSHOT
    assert result.symbol == symbol


def _assert_exposure(result: ParsedIntent) -> None:
    assert result.intent == Intent.EXPOSURE


def _assert_digest(result: ParsedIntent, symbol: str | None = None) -> None:
    assert result.intent == Intent.JOURNAL_DIGEST
    assert result.symbol == symbol


def _assert_help(result: ParsedIntent) -> None:
    assert result.intent == Intent.HELP


# --- /brief ---


def test_slash_brief_with_symbol() -> None:
    _assert_brief(parse_intent("/brief BBRI"), "BBRI")


def test_slash_brief_lowercase() -> None:
    _assert_brief(parse_intent("/brief bbri"), "BBRI")


def test_slash_brf_alias() -> None:
    _assert_brief(parse_intent("/brf BBRI"), "BBRI")


def test_slash_brief_extra_whitespace() -> None:
    _assert_brief(parse_intent("  /brief  BBRI  "), "BBRI")


# --- /ticker ---


def test_slash_ticker_with_symbol() -> None:
    _assert_ticker(parse_intent("/ticker BBRI"), "BBRI")


def test_slash_tck_alias() -> None:
    _assert_ticker(parse_intent("/tck BBRI"), "BBRI")


def test_slash_t_alias() -> None:
    _assert_ticker(parse_intent("/t BBRI"), "BBRI")


# --- /alert ---


def test_slash_alert_list() -> None:
    result = parse_intent("/alert list")
    assert result.intent == Intent.ALERT_TRIAGE
    assert result.alert_action == "list"


def test_slash_alert_acknowledge() -> None:
    result = parse_intent("/alert ack evt-123")
    assert result.intent == Intent.ALERT_TRIAGE
    assert result.alert_action == "ack"
    assert result.alert_event_id == "evt-123"


def test_slash_al_short() -> None:
    result = parse_intent("/al fp evt-456")
    assert result.intent == Intent.ALERT_TRIAGE
    assert result.alert_action == "fp"
    assert result.alert_event_id == "evt-456"


# --- /journal ---


def test_slash_journal_with_text() -> None:
    result = parse_intent("/journal Market was volatile today")
    assert result.intent == Intent.JOURNAL_CAPTURE
    assert result.journal_text is not None
    assert "Market was volatile today" in result.journal_text


def test_slash_jrn_alias() -> None:
    result = parse_intent("/jrn Test entry")
    assert result.intent == Intent.JOURNAL_CAPTURE
    assert result.journal_text == "Test entry"


# --- /research ---


def test_slash_research_with_symbol_and_note() -> None:
    result = parse_intent("/research BBRI check dividend history")
    assert result.intent == Intent.RESEARCH_ADD
    assert result.research_symbol == "BBRI"
    assert result.research_note == "check dividend history"


def test_slash_res_alias() -> None:
    result = parse_intent("/res TLKM perlu cek kompetitor")
    assert result.intent == Intent.RESEARCH_ADD
    assert result.research_symbol == "TLKM"


# --- /exposure ---


def test_slash_exposure() -> None:
    _assert_exposure(parse_intent("/exposure"))


def test_slash_exp_alias() -> None:
    _assert_exposure(parse_intent("/exp"))


def test_slash_port_alias() -> None:
    _assert_exposure(parse_intent("/port"))


# --- /digest ---


def test_slash_digest() -> None:
    _assert_digest(parse_intent("/digest"))


def test_slash_digest_with_symbol() -> None:
    _assert_digest(parse_intent("/digest BBRI"), "BBRI")


def test_slash_dg_no_symbol() -> None:
    _assert_digest(parse_intent("/dg"))


def test_slash_dg_with_symbol() -> None:
    _assert_digest(parse_intent("/dg TLKM"), "TLKM")


# --- /help ---


def test_slash_help() -> None:
    _assert_help(parse_intent("/help"))


def test_slash_h() -> None:
    _assert_help(parse_intent("/h"))


# --- Natural language ---


def test_nl_brief_on_symbol() -> None:
    _assert_brief(parse_intent("brief on BBRI"), "BBRI")


def test_nl_brief_symbol() -> None:
    _assert_brief(parse_intent("brief BBRI"), "BBRI")


def test_nl_ticker_symbol() -> None:
    _assert_ticker(parse_intent("ticker BBRI"), "BBRI")


def test_nl_snapshot_of_symbol() -> None:
    _assert_ticker(parse_intent("snapshot of TLKM"), "TLKM")


def test_nl_exposure() -> None:
    _assert_exposure(parse_intent("exposure"))


def test_nl_portfolio() -> None:
    _assert_exposure(parse_intent("portfolio"))


def test_nl_my_portfolio() -> None:
    _assert_exposure(parse_intent("my portfolio"))


def test_nl_digest() -> None:
    _assert_digest(parse_intent("digest"))


def test_nl_journal_summary() -> None:
    _assert_digest(parse_intent("journal summary"))


def test_nl_digest_with_symbol() -> None:
    _assert_digest(parse_intent("digest BBRI"), "BBRI")


def test_nl_help() -> None:
    _assert_help(parse_intent("help"))


def test_nl_question_mark() -> None:
    _assert_help(parse_intent("?"))


# --- Unknown ---


def test_unknown_empty_string() -> None:
    result = parse_intent("")
    assert result.intent == Intent.UNKNOWN


def test_unknown_whitespace_only() -> None:
    result = parse_intent("   ")
    assert result.intent == Intent.UNKNOWN


def test_unknown_random_text() -> None:
    result = parse_intent("how is the weather today")
    assert result.intent == Intent.UNKNOWN


def test_unknown_gibberish_command() -> None:
    result = parse_intent("/foobar xyz")
    assert result.intent == Intent.UNKNOWN


def test_brief_without_symbol_returns_brief_with_none() -> None:
    result = parse_intent("/brief")
    assert result.intent == Intent.BRIEF
    assert result.symbol is None


def test_unknown_invalid_ticker_length() -> None:
    result = parse_intent("/brief ABCDEX")
    assert result.intent == Intent.UNKNOWN


def test_raw_text_preserved() -> None:
    result = parse_intent("/brief BBRI")
    assert result.raw_text == "/brief BBRI"


def test_raw_text_unknown() -> None:
    result = parse_intent("some random stuff")
    assert result.raw_text == "some random stuff"
