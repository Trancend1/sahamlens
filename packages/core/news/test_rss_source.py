"""RSSNewsSource adapter — never raises, classifies status correctly."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from packages.core.news.rss_source import RSSNewsSource


class _FakeFeedEntry:
    def __init__(
        self,
        *,
        link: str,
        title: str,
        published: str = "Mon, 18 May 2026 12:00:00 +0700",
        summary: str | None = "Ringkasan singkat.",
    ) -> None:
        self.link = link
        self.title = title
        self.published = published
        self.summary = summary


class _FakeFeed:
    def __init__(self, entries: list[_FakeFeedEntry]) -> None:
        self.entries = entries


def _make_source(
    *,
    fetcher: Callable[[str], bytes],
    parser_entries: list[_FakeFeedEntry] | None = None,
    parser: Callable[[bytes], Any] | None = None,
) -> RSSNewsSource:
    clock = [0.0]

    def fake_clock() -> float:
        clock[0] += 1.0
        return clock[0]

    return RSSNewsSource(
        {"detik": "https://example.test/rss"},
        min_interval_s=0.0,
        backoff_s=(),
        fetcher=fetcher,
        parser=parser or (lambda _: _FakeFeed(parser_entries or [])),
        clock=fake_clock,
    )


def test_fetch_ok_with_entries() -> None:
    src = _make_source(
        fetcher=lambda _url: b"<rss/>",
        parser_entries=[
            _FakeFeedEntry(link="https://detik.com/a", title="A"),
            _FakeFeedEntry(link="https://detik.com/b", title="B"),
        ],
    )
    results = src.fetch()
    assert len(results) == 1
    r = results[0]
    assert r.status == "ok"
    assert len(r.articles) == 2
    assert r.error_message is None


def test_fetch_partial_when_zero_entries() -> None:
    src = _make_source(fetcher=lambda _url: b"<rss/>", parser_entries=[])
    results = src.fetch()
    assert results[0].status == "partial"
    assert results[0].articles == []


def test_fetch_failed_when_http_error() -> None:
    def broken_fetcher(_url: str) -> bytes:
        raise OSError("connection refused")

    src = _make_source(fetcher=broken_fetcher)
    results = src.fetch()
    assert results[0].status == "failed"
    assert results[0].error_message is not None
    assert "connection refused" in results[0].error_message


def test_fetch_dedups_within_feed() -> None:
    src = _make_source(
        fetcher=lambda _url: b"<rss/>",
        parser_entries=[
            _FakeFeedEntry(link="https://detik.com/a?utm_source=x", title="A"),
            _FakeFeedEntry(link="https://detik.com/a?utm_source=y", title="A duplicate"),
        ],
    )
    results = src.fetch()
    assert len(results[0].articles) == 1


def test_constructor_rejects_empty_feed_urls() -> None:
    with pytest.raises(ValueError):
        RSSNewsSource({})


def test_entries_without_link_or_title_skipped() -> None:
    src = _make_source(
        fetcher=lambda _url: b"<rss/>",
        parser_entries=[
            _FakeFeedEntry(link="", title="A"),
            _FakeFeedEntry(link="https://detik.com/b", title=""),
            _FakeFeedEntry(link="https://detik.com/c", title="C"),
        ],
    )
    results = src.fetch()
    assert len(results[0].articles) == 1
    assert results[0].articles[0].title == "C"
