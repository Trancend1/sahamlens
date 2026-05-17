"""Tests for canonical ticker normalize."""

from __future__ import annotations

import pytest
from packages.core.data_sources.normalize import normalize_ticker


def test_already_canonical() -> None:
    assert normalize_ticker("BBCA.JK") == "BBCA.JK"


def test_lowercase_normalized() -> None:
    assert normalize_ticker("bbca.jk") == "BBCA.JK"


def test_suffix_added_when_missing() -> None:
    assert normalize_ticker("BBCA") == "BBCA.JK"


def test_whitespace_trimmed() -> None:
    assert normalize_ticker("  TLKM.JK  ") == "TLKM.JK"


def test_alphanumeric_4chars_ok() -> None:
    assert normalize_ticker("ANTM") == "ANTM.JK"


@pytest.mark.parametrize(
    "bad",
    ["", "BBC", "BBCAA", "BBCA.JKX", "BBCA.US", "BB-CA.JK", "  ", "BB CA"],
)
def test_invalid_rejected(bad: str) -> None:
    with pytest.raises(ValueError):
        normalize_ticker(bad)


def test_non_string_rejected() -> None:
    with pytest.raises(ValueError):
        normalize_ticker(None)  # type: ignore[arg-type]
