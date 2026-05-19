"""Unit tests for canonical_url + article_id."""

from __future__ import annotations

import pytest
from packages.core.news.dedup import article_id, canonical_url


def test_strips_utm_and_fbclid_params() -> None:
    raw = "https://finance.detik.com/news?id=42&utm_source=twitter&fbclid=abc"
    assert canonical_url(raw) == "https://finance.detik.com/news?id=42"


def test_drops_fragment_and_trailing_slash() -> None:
    raw = "https://Finance.Detik.COM/news/42/#section"
    assert canonical_url(raw) == "https://finance.detik.com/news/42"


def test_keeps_root_path_slash() -> None:
    assert canonical_url("https://example.com/") == "https://example.com/"


def test_lowercases_host_preserves_path_case() -> None:
    raw = "https://CNBC.com/Path/Page"
    assert canonical_url(raw) == "https://cnbc.com/Path/Page"


def test_normalizes_query_param_ordering() -> None:
    a = canonical_url("https://x.com/a?b=1&a=2")
    b = canonical_url("https://x.com/a?a=2&b=1")
    assert a == b


def test_rejects_missing_scheme() -> None:
    with pytest.raises(ValueError):
        canonical_url("//no-scheme.com/x")


def test_rejects_empty_string() -> None:
    with pytest.raises(ValueError):
        canonical_url("")


def test_article_id_is_stable_for_same_url() -> None:
    canonical = canonical_url("https://x.com/a")
    assert article_id(canonical) == article_id(canonical)


def test_article_id_fits_bigint() -> None:
    canonical = canonical_url("https://x.com/very/long/path?a=1&b=2&c=3")
    assert 0 <= article_id(canonical) < 2**60


def test_article_id_differs_per_url() -> None:
    a = article_id(canonical_url("https://x.com/a"))
    b = article_id(canonical_url("https://x.com/b"))
    assert a != b
