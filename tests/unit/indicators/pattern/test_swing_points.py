"""Tests for swing_points indicator."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.pattern import swing_high_at, swing_highs, swing_low_at, swing_lows, swing_points
from laakhay.ta.registry.models import SeriesContext


def _make_price_series(
    values: list[int | float | Decimal],
    *,
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
) -> Series[Price]:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = tuple(base + timedelta(hours=i) for i in range(len(values)))
    return Series[Price](
        timestamps=timestamps,
        values=tuple(Decimal(str(v)) for v in values),
        symbol=symbol,
        timeframe=timeframe,
    )


def test_swing_points_flags_basic_detection():
    high = _make_price_series([1, 2, 3, 2, 1, 2, 4, 2, 1])
    low = _make_price_series([1, 0, 1, 0, -1, 0, 1, 0, -1])
    ctx = SeriesContext(high=high, low=low)

    result = swing_points(ctx, left=1, right=1, return_mode="flags")

    high_series = result["swing_high"]
    low_series = result["swing_low"]

    assert high_series.values == (
        False,
        False,
        True,
        False,
        False,
        False,
        True,
        False,
        False,
    )
    assert low_series.values == (
        False,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        False,
    )
    assert high_series.availability_mask == (
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
    )
    assert low_series.availability_mask == (
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
    )


def test_swing_points_levels_reference_prices():
    high = _make_price_series([1, 2, 3, 2, 1, 2, 4, 2, 1])
    low = _make_price_series([1, 0, 1, 0, -1, 0, 1, 0, -1])
    ctx = SeriesContext(high=high, low=low)

    result = swing_points(ctx, left=1, right=1, return_mode="levels")

    high_series = result["swing_high"]
    low_series = result["swing_low"]

    # Masks only flag confirmed swing candles
    assert high_series.availability_mask == (
        False,
        False,
        True,
        False,
        False,
        False,
        True,
        False,
        False,
    )
    assert low_series.availability_mask == (
        False,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        False,
    )

    # Values inherit underlying price series
    assert high_series.values == high.values
    assert low_series.values == low.values


def test_swing_points_equal_highs_not_flagged():
    high = _make_price_series([1, 3, 3, 2])
    low = _make_price_series([0, -1, -1, 0])
    ctx = SeriesContext(high=high, low=low)

    result = swing_points(ctx, left=1, right=1)

    assert all(not flag for flag in result["swing_high"].values)
    # lows still have no unique minima: both -1 duplicates
    assert all(not flag for flag in result["swing_low"].values)


def test_swing_points_equal_extremes_allowed():
    high = _make_price_series([1, 3, 3, 2, 1])
    low = _make_price_series([0, -1, -1, 0, 1])
    ctx = SeriesContext(high=high, low=low)

    result = swing_points(ctx, left=1, right=1, allow_equal_extremes=True)

    assert any(result["swing_high"].values)


def test_swing_at_indexed_levels():
    high = _make_price_series([1, 2, 3, 2, 1, 2, 4, 2, 1, 2, 5, 2])
    low = _make_price_series([1, 0, 1, 0, -1, 0, 1, 0, -1, 0, 1, 0])
    ctx = SeriesContext(high=high, low=low)

    latest_high = swing_high_at(ctx, index=1, left=1, right=1)
    prev_high = swing_high_at(ctx, index=2, left=1, right=1)
    latest_low = swing_low_at(ctx, index=1, left=1, right=1)

    assert latest_high.availability_mask[-1]
    assert prev_high.availability_mask[-1]
    assert latest_low.availability_mask[-1]
    assert latest_high.values[-1] == Decimal("5")
    assert prev_high.values[-1] == Decimal("4")
    assert latest_low.values[-1] == Decimal("-1")


def test_swing_at_invalid_index():
    high = _make_price_series([1, 2, 3, 2, 1])
    low = _make_price_series([1, 0, 1, 0, -1])
    ctx = SeriesContext(high=high, low=low)

    with pytest.raises(ValueError):
        swing_high_at(ctx, index=0, left=1, right=1)


def test_swing_highs_direct_api_levels():
    high = _make_price_series([1, 2, 3, 2, 1, 2, 4, 2, 1])
    low = _make_price_series([1, 0, 1, 0, -1, 0, 1, 0, -1])
    ctx = SeriesContext(high=high, low=low)

    levels = swing_highs(ctx, left=1, right=1, return_mode="levels")
    flags = swing_highs(ctx, left=1, right=1, return_mode="flags")

    # Levels inherit prices but only mark confirmed swing highs in availability mask.
    assert levels.values == high.values
    assert levels.availability_mask == (
        False,
        False,
        True,
        False,
        False,
        False,
        True,
        False,
        False,
    )
    # Flags represent the same pattern as swing_points overall result.
    assert flags.values == (False, False, True, False, False, False, True, False, False)


def test_swing_lows_direct_api_levels():
    high = _make_price_series([1, 2, 3, 2, 1, 2, 4, 2, 1])
    low = _make_price_series([1, 0, 1, 0, -1, 0, 1, 0, -1])
    ctx = SeriesContext(high=high, low=low)

    levels = swing_lows(ctx, left=1, right=1, return_mode="levels")
    flags = swing_lows(ctx, left=1, right=1, return_mode="flags")

    assert levels.values == low.values
    assert levels.availability_mask == (
        False,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        False,
    )
    assert flags.values == (
        False,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        False,
    )


def test_swing_points_insufficient_history():
    high = _make_price_series([1, 2, 3, 2])
    low = _make_price_series([1, 0, -1, 0])
    ctx = SeriesContext(high=high, low=low)

    result = swing_points(ctx, left=2, right=2)

    assert result["swing_high"].availability_mask == (False, False, False, False)
    assert result["swing_low"].availability_mask == (False, False, False, False)


def test_swing_points_invalid_params():
    high = _make_price_series([1, 2, 3])
    low = _make_price_series([0, -1, 0])
    ctx = SeriesContext(high=high, low=low)

    with pytest.raises(ValueError):
        swing_points(ctx, left=0, right=1)

    with pytest.raises(ValueError):
        swing_points(SeriesContext(low=low), left=1, right=1)

    with pytest.raises(ValueError):
        swing_points(ctx, return_mode="unknown")  # type: ignore[arg-type]
