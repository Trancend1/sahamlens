"""CSV portfolio importer with auto-detect and manual field-map fallback.

Auto-detect scans column names for canonical aliases:
  symbol : symbol | kode | ticker | emiten | saham
  lots   : lots | lot | lembar
  price  : avg_price | avg | harga | price | harga_beli | rata_rata

If all 3 map unambiguously → ImportResult with positions populated.
If any column is missing/ambiguous → ImportResult with empty positions,
  warnings describing the issue, and field_map containing detected columns
  so the caller can present a field-mapper UI and re-call with explicit map.
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from packages.core.data_sources.normalize import normalize_ticker
from packages.core.portfolio.models import PortfolioPosition

log = logging.getLogger(__name__)

_SYMBOL_ALIASES = {"symbol", "kode", "ticker", "emiten", "saham"}
_LOTS_ALIASES = {"lots", "lot", "lembar"}
_PRICE_ALIASES = {"avg_price", "avg", "harga", "price", "harga_beli", "rata_rata"}


@dataclass
class ImportResult:
    positions: list[PortfolioPosition]
    warnings: list[str]
    field_map: dict[str, str]  # canonical name → detected CSV column header
    detected_columns: list[str]  # raw CSV headers, for field-mapper UI


def parse_csv(
    content: str,
    field_map: dict[str, str] | None = None,
) -> ImportResult:
    """Parse CSV content into portfolio positions.

    Args:
        content: Raw CSV text.
        field_map: Optional explicit mapping {canonical → csv_column}.
                   If None, auto-detect from column names.
    Returns:
        ImportResult. positions is empty if detection failed or all rows invalid.
    """
    reader = csv.DictReader(io.StringIO(content.strip()))
    if reader.fieldnames is None:
        return ImportResult(
            positions=[],
            warnings=["CSV kosong atau tidak memiliki header."],
            field_map={},
            detected_columns=[],
        )

    columns = [c.strip().lower() for c in reader.fieldnames]
    raw_columns = list(reader.fieldnames)

    resolved_map, warnings = _resolve_field_map(columns, raw_columns, field_map)
    if warnings:
        return ImportResult(
            positions=[],
            warnings=warnings,
            field_map=resolved_map,
            detected_columns=raw_columns,
        )

    positions: list[PortfolioPosition] = []
    row_warnings: list[str] = []
    now = datetime.now(UTC)

    for i, row in enumerate(reader, start=2):
        result = _parse_row(row, resolved_map, now, i)
        if isinstance(result, str):
            row_warnings.append(result)
            log.warning("portfolio_import row_skip row=%d reason=%s", i, result)
        else:
            positions.append(result)

    return ImportResult(
        positions=positions,
        warnings=row_warnings,
        field_map=resolved_map,
        detected_columns=raw_columns,
    )


def _resolve_field_map(
    columns: list[str],
    raw_columns: list[str],
    explicit: dict[str, str] | None,
) -> tuple[dict[str, str], list[str]]:
    """Return (resolved_map, warnings). resolved_map maps canonical → raw_column."""
    if explicit:
        missing = [k for k in ("symbol", "lots", "price") if k not in explicit]
        if missing:
            return {}, [f"field_map tidak lengkap, kolom hilang: {missing}"]
        # validate that mapped columns actually exist in CSV (case-insensitive)
        col_lower = {c.lower(): c for c in raw_columns}
        resolved: dict[str, str] = {}
        errs: list[str] = []
        for canonical, user_col in explicit.items():
            match = col_lower.get(user_col.lower())
            if not match:
                errs.append(f"Kolom '{user_col}' tidak ditemukan di CSV.")
            else:
                resolved[canonical] = match
        return resolved, errs

    col_lower_map = {c: raw for c, raw in zip(columns, raw_columns, strict=False)}
    sym = _first_match(col_lower_map, _SYMBOL_ALIASES)
    lots = _first_match(col_lower_map, _LOTS_ALIASES)
    price = _first_match(col_lower_map, _PRICE_ALIASES)

    warnings: list[str] = []
    if not sym:
        warnings.append(
            f"Kolom symbol tidak ditemukan. Tersedia: {raw_columns}. "
            "Alias yang dikenali: symbol, kode, ticker, emiten, saham."
        )
    if not lots:
        warnings.append(
            f"Kolom lots tidak ditemukan. Tersedia: {raw_columns}. "
            "Alias yang dikenali: lots, lot, lembar."
        )
    if not price:
        warnings.append(
            f"Kolom harga beli tidak ditemukan. Tersedia: {raw_columns}. "
            "Alias yang dikenali: avg_price, avg, harga, price, harga_beli, rata_rata."
        )

    resolved_map: dict[str, str] = {}
    if sym:
        resolved_map["symbol"] = sym
    if lots:
        resolved_map["lots"] = lots
    if price:
        resolved_map["price"] = price

    return resolved_map, warnings


def _first_match(col_map: dict[str, str], aliases: set[str]) -> str | None:
    for alias in aliases:
        if alias in col_map:
            return col_map[alias]
    return None


def _parse_row(
    row: dict[str, str | None],
    field_map: dict[str, str],
    imported_at: datetime,
    row_num: int,
) -> PortfolioPosition | str:
    """Return PortfolioPosition or error string if row is invalid."""
    raw_symbol = (row.get(field_map["symbol"]) or "").strip()
    raw_lots = (row.get(field_map["lots"]) or "").strip()
    raw_price = (row.get(field_map["price"]) or "").strip()

    if not raw_symbol:
        return f"Baris {row_num}: symbol kosong, dilewati."

    try:
        symbol = normalize_ticker(raw_symbol)
    except ValueError as e:
        return f"Baris {row_num}: ticker tidak valid '{raw_symbol}' — {e}"

    try:
        lots = int(raw_lots.replace(",", "").replace(".", ""))
    except ValueError:
        return f"Baris {row_num}: lots tidak valid '{raw_lots}'"

    if lots <= 0:
        return f"Baris {row_num}: lots harus > 0, got {lots}"

    try:
        price = float(raw_price.replace(",", "").replace(".", "."))
    except ValueError:
        return f"Baris {row_num}: harga tidak valid '{raw_price}'"

    if price <= 0:
        return f"Baris {row_num}: harga harus > 0, got {price}"

    return PortfolioPosition(
        symbol=symbol,
        lots=lots,
        avg_price=price,
        imported_at=imported_at,
        source="csv",
    )
