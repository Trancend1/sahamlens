"""Brief message formatting: includes evidence/freshness/disclaimer, no signal language."""

from __future__ import annotations

from packages.core.agent.brief_delivery import DISCLAIMER, format_brief_message
from packages.core.ai.models import EvidenceItem, StockBrief
from packages.core.ai.validator import scan_banned


def _sample_brief() -> StockBrief:
    return StockBrief(
        symbol="BBCA.JK",
        analysis_date="2026-06-15",
        prompt_template_id="stock_brief@1",
        model="claude",
        evidence=[
            EvidenceItem(
                type="price",
                value="Harga menutup mendekati rata-rata 20 hari",
                source_ref="price_history",
                freshness="2026-06-14T00:00:00+00:00",
            ),
            EvidenceItem(
                type="fundamental",
                value="Data ROE periode terakhir belum lengkap",
                source_ref="fundamental_snapshots",
                freshness="2026-03-31T00:00:00+00:00",
            ),
        ],
        bullish_view="Volume di atas rata-rata pekan ini, tren jangka pendek menguat.",
        bearish_view="Konfirmasi volume lemah dan sebagian data fundamental belum lengkap.",
        uncertainty="Data fundamental terbaru belum tersedia, sehingga gambaran masih parsial.",
        caveats=["Sebagian data stale", "Belum ada konfirmasi earnings terbaru"],
        beginner_explanation="Konteks ini menjelaskan kondisi data, bukan ajakan transaksi.",
        suggested_next_question="Apakah konfirmasi volume bertahan setelah rilis berita terbaru?",
    )


def test_message_contains_core_sections() -> None:
    message = format_brief_message(_sample_brief())
    assert "BBCA.JK" in message
    assert "2026-06-15" in message
    assert "Evidence:" in message
    assert "freshness: 2026-06-14T00:00:00+00:00" in message
    assert "Caveat:" in message
    assert "Sebagian data stale" in message
    assert DISCLAIMER in message


def test_message_has_no_signal_language() -> None:
    message = format_brief_message(_sample_brief())
    assert scan_banned(message) is None


def test_wrapper_copy_itself_is_clean() -> None:
    # The disclaimer and labels we add must not trip the banned-phrase filter.
    assert scan_banned(DISCLAIMER) is None
