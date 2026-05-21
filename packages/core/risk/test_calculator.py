"""Unit + property tests for position_size calculator. Coverage gate ≥90%."""

from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from packages.core.risk.calculator import PositionSizeResult, position_size

# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


def test_golden_known_inputs() -> None:
    # portfolio=100jt, risk=1%, entry=1000, stop=950 → 200 lots
    result = position_size(
        portfolio_value=100_000_000,
        risk_percent=0.01,
        entry_price=1000.0,
        stop_price=950.0,
    )
    assert result.lots == 200
    assert result.position_size_rupiah == 20_000_000
    assert result.max_loss_rupiah == 1_000_000
    assert result.risk_rupiah == 1_000_000


def test_stop_above_entry_returns_zero_lots() -> None:
    result = position_size(
        portfolio_value=100_000_000,
        risk_percent=0.01,
        entry_price=1000.0,
        stop_price=1050.0,
    )
    assert result.lots == 0
    assert result.position_size_rupiah == 0
    assert result.max_loss_rupiah == 0


def test_stop_equal_entry_returns_zero_lots() -> None:
    result = position_size(
        portfolio_value=100_000_000,
        risk_percent=0.01,
        entry_price=1000.0,
        stop_price=1000.0,
    )
    assert result.lots == 0


def test_zero_risk_percent_returns_zero_lots() -> None:
    result = position_size(
        portfolio_value=100_000_000,
        risk_percent=0.0,
        entry_price=1000.0,
        stop_price=950.0,
    )
    assert result.lots == 0
    assert result.risk_rupiah == 0


def test_negative_risk_percent_returns_zero_lots() -> None:
    result = position_size(
        portfolio_value=100_000_000,
        risk_percent=-0.01,
        entry_price=1000.0,
        stop_price=950.0,
    )
    assert result.lots == 0


def test_tight_stop_yields_large_lots() -> None:
    # entry=1000, stop=999 (Rp1 diff) → risk_per_lot=100
    # risk=100_000 → lots=1000
    result = position_size(
        portfolio_value=100_000_000,
        risk_percent=0.001,
        entry_price=1000.0,
        stop_price=999.0,
    )
    assert result.lots == 1000
    assert result.max_loss_rupiah == 100_000


def test_large_portfolio_small_risk_scales_correctly() -> None:
    # portfolio=10B, risk=0.5%, entry=5000, stop=4800
    # risk_rupiah=50_000_000, risk_per_lot=200*100=20000 → lots=2500
    result = position_size(
        portfolio_value=10_000_000_000,
        risk_percent=0.005,
        entry_price=5000.0,
        stop_price=4800.0,
    )
    assert result.lots == 2500
    assert result.max_loss_rupiah == 50_000_000


def test_return_type_is_position_size_result() -> None:
    result = position_size(
        portfolio_value=100_000_000,
        risk_percent=0.01,
        entry_price=1000.0,
        stop_price=950.0,
    )
    assert isinstance(result, PositionSizeResult)


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------

_valid_inputs = st.fixed_dictionaries(
    {
        "portfolio_value": st.integers(min_value=1_000_000, max_value=100_000_000_000),
        "risk_percent": st.floats(min_value=0.001, max_value=0.05, allow_nan=False),
        "entry_price": st.floats(min_value=50.0, max_value=100_000.0, allow_nan=False),
        "stop_offset": st.floats(min_value=1.0, max_value=500.0, allow_nan=False),
    }
)


@given(_valid_inputs)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_max_loss_never_exceeds_risk_rupiah(inputs: dict[str, int | float]) -> None:
    result = position_size(
        portfolio_value=int(inputs["portfolio_value"]),
        risk_percent=float(inputs["risk_percent"]),
        entry_price=float(inputs["entry_price"]),
        stop_price=float(inputs["entry_price"]) - float(inputs["stop_offset"]),
    )
    assert result.max_loss_rupiah <= result.risk_rupiah


@given(_valid_inputs)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_position_size_rupiah_non_negative(inputs: dict[str, int | float]) -> None:
    result = position_size(
        portfolio_value=int(inputs["portfolio_value"]),
        risk_percent=float(inputs["risk_percent"]),
        entry_price=float(inputs["entry_price"]),
        stop_price=float(inputs["entry_price"]) - float(inputs["stop_offset"]),
    )
    assert result.position_size_rupiah >= 0
    assert result.lots >= 0


@given(
    st.integers(min_value=1_000_000, max_value=10_000_000_000),
    st.floats(min_value=100.0, max_value=50_000.0, allow_nan=False),
    st.floats(min_value=1.0, max_value=200.0, allow_nan=False),
    st.floats(min_value=0.001, max_value=0.02, allow_nan=False),
    st.floats(min_value=0.021, max_value=0.05, allow_nan=False),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_higher_risk_percent_yields_more_or_equal_lots(
    portfolio: int,
    entry: float,
    stop_offset: float,
    low_risk: float,
    high_risk: float,
) -> None:
    stop = entry - stop_offset
    low = position_size(portfolio, low_risk, entry, stop)
    high = position_size(portfolio, high_risk, entry, stop)
    assert high.lots >= low.lots


@given(
    st.integers(min_value=1_000_000, max_value=10_000_000_000),
    st.floats(min_value=200.0, max_value=50_000.0, allow_nan=False),
    st.floats(min_value=1.0, max_value=50.0, allow_nan=False),
    st.floats(min_value=51.0, max_value=200.0, allow_nan=False),
    st.floats(min_value=0.001, max_value=0.05, allow_nan=False),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_larger_stop_distance_yields_fewer_or_equal_lots(
    portfolio: int,
    entry: float,
    small_offset: float,
    large_offset: float,
    risk: float,
) -> None:
    tight = position_size(portfolio, risk, entry, entry - small_offset)
    wide = position_size(portfolio, risk, entry, entry - large_offset)
    assert wide.lots <= tight.lots
