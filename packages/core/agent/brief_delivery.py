"""Format a StockBrief into a calm, evidence-based message (ADR-0019 M0).

Pure formatting reused by the M0 pull CLI and the future Hermes runtime (M4).
The brief fields are already validated against banned-phrase rules upstream;
this wrapper adds only neutral labels and a non-financial-advice disclaimer, and
must never introduce buy/sell/target instruction language.
"""

from __future__ import annotations

from packages.core.ai.models import StockBrief

DISCLAIMER = (
    "Bukan nasihat keuangan. Ini decision support berbasis data lokal; "
    "verifikasi freshness dan ambil keputusan sendiri."
)


def format_brief_message(brief: StockBrief) -> str:
    """Render a StockBrief as plain text suitable for Telegram/CLI output."""
    lines: list[str] = [
        f"SahamLens brief — {brief.symbol}",
        f"Tanggal analisis: {brief.analysis_date}",
        "",
        f"Konteks pendukung: {brief.bullish_view}",
        f"Konteks risiko: {brief.bearish_view}",
        f"Ketidakpastian: {brief.uncertainty}",
        "",
        "Evidence:",
    ]
    lines.extend(
        f"- [{item.type}] {item.value} (sumber: {item.source_ref}, freshness: {item.freshness})"
        for item in brief.evidence
    )
    if brief.caveats:
        lines.append("")
        lines.append("Caveat:")
        lines.extend(f"- {caveat}" for caveat in brief.caveats)
    lines.extend(
        [
            "",
            f"Penjelasan: {brief.beginner_explanation}",
            f"Pertanyaan lanjutan: {brief.suggested_next_question}",
            "",
            DISCLAIMER,
        ]
    )
    return "\n".join(lines)
