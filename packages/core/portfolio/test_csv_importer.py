"""Contract tests for csv_importer using fixture files."""

from __future__ import annotations

from pathlib import Path

from packages.core.portfolio.csv_importer import parse_csv

FIXTURES = Path(__file__).parent / "tests" / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestAutoDetect:
    def test_valid_csv_parses_all_rows(self) -> None:
        result = parse_csv(_read("valid.csv"))
        assert len(result.positions) == 3
        assert not result.warnings
        syms = {p.symbol for p in result.positions}
        assert syms == {"BBCA.JK", "BBRI.JK", "TLKM.JK"}

    def test_valid_csv_values(self) -> None:
        result = parse_csv(_read("valid.csv"))
        bbca = next(p for p in result.positions if p.symbol == "BBCA.JK")
        assert bbca.lots == 10
        assert bbca.avg_price == 9200.0
        assert bbca.source == "csv"

    def test_broker_format_extra_columns_ignored(self) -> None:
        result = parse_csv(_read("broker_format.csv"))
        assert len(result.positions) == 3
        assert not result.warnings
        assert all(p.symbol.endswith(".JK") for p in result.positions)

    def test_bad_headers_returns_empty_with_warnings(self) -> None:
        result = parse_csv(_read("bad_headers.csv"))
        assert result.positions == []
        assert len(result.warnings) >= 1
        # should contain partial field_map or empty
        assert "detected_columns" in dir(result)

    def test_empty_csv_returns_warning(self) -> None:
        result = parse_csv("")
        assert result.positions == []
        assert result.warnings

    def test_header_only_csv_returns_no_positions(self) -> None:
        result = parse_csv("symbol,lots,avg_price\n")
        assert result.positions == []
        assert not result.warnings  # header detected fine, just no rows

    def test_lots_zero_produces_warning(self) -> None:
        csv = "symbol,lots,avg_price\nBBCA,0,9200\n"
        result = parse_csv(csv)
        assert result.positions == []
        assert any("lots" in w.lower() or "0" in w for w in result.warnings)

    def test_negative_price_produces_warning(self) -> None:
        csv = "symbol,lots,avg_price\nBBCA,10,-100\n"
        result = parse_csv(csv)
        assert result.positions == []
        assert result.warnings

    def test_invalid_ticker_produces_warning(self) -> None:
        csv = "symbol,lots,avg_price\nTOOLONGTICKER,10,1000\n"
        result = parse_csv(csv)
        assert result.positions == []
        assert result.warnings

    def test_mixed_good_bad_rows(self) -> None:
        csv = "symbol,lots,avg_price\nBBCA,10,9200\nBAD!!,5,1000\nBBRI,3,4500\n"
        result = parse_csv(csv)
        assert len(result.positions) == 2
        assert len(result.warnings) == 1

    def test_ticker_normalized(self) -> None:
        csv = "symbol,lots,avg_price\nbbca,10,9200\n"
        result = parse_csv(csv)
        assert result.positions[0].symbol == "BBCA.JK"

    def test_alias_kode(self) -> None:
        csv = "kode,lots,avg_price\nBBCA,10,9200\n"
        result = parse_csv(csv)
        assert len(result.positions) == 1

    def test_alias_lot_singular(self) -> None:
        csv = "symbol,lot,avg_price\nBBCA,10,9200\n"
        result = parse_csv(csv)
        assert len(result.positions) == 1

    def test_alias_harga(self) -> None:
        csv = "symbol,lots,harga\nBBCA,10,9200\n"
        result = parse_csv(csv)
        assert len(result.positions) == 1


class TestExplicitFieldMap:
    def test_explicit_field_map_overrides_detection(self) -> None:
        content = _read("bad_headers.csv")
        result = parse_csv(
            content, field_map={"symbol": "kode_saham", "lots": "jumlah", "price": "harga_rata"}
        )
        assert len(result.positions) == 2
        assert not result.warnings

    def test_explicit_map_missing_key_returns_error(self) -> None:
        result = parse_csv("a,b,c\n1,2,3\n", field_map={"symbol": "a", "lots": "b"})
        assert result.positions == []
        assert result.warnings

    def test_explicit_map_nonexistent_column_returns_error(self) -> None:
        csv = "symbol,lots,avg_price\nBBCA,10,9200\n"
        result = parse_csv(
            csv, field_map={"symbol": "symbol", "lots": "lots", "price": "NO_SUCH_COL"}
        )
        assert result.positions == []
        assert result.warnings
