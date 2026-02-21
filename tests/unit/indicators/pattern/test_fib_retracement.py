"""Tests for fib_retracement indicator."""

from datetime import UTC, datetime, timedelta

UTC = UTC
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.pattern import (
    fib_anchor_high,
    fib_anchor_low,
    fib_level_down,
    fib_level_up,
    fib_retracement,
)
from laakhay.ta.registry.models import SeriesContext


def _series(
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


def test_fib_retracement_down_levels():
    # Construct highs/lows with a clear swing low then swing high
    highs = _series([10, 12, 15, 12, 11, 16, 18, 17, 16])
    lows = _series([8, 9, 11, 10, 9, 12, 14, 13, 12])
    ctx = SeriesContext(high=highs, low=lows)

    result = fib_retracement(ctx, left=1, right=1, levels=(0.618, 0.5))

    down = result["down"]
    anchor_high = result["anchor_high"]
    anchor_low = result["anchor_low"]

    level_618 = down["0.618"]
    level_50 = down["0.5"]

    # Latest confirmed swing high (idx=6, price=18) after swing low (idx=4, price=9)
    assert anchor_high.values[-1] == Decimal("18")
    assert anchor_low.values[-1] == Decimal("9")

    # 61.8% retracement: high - (high-low)*0.618 = 18 - 9*0.618
    expected_618 = Decimal("18") - (Decimal("18") - Decimal("9")) * Decimal("0.618")
    assert level_618.values[-1].quantize(Decimal("0.0001")) == expected_618.quantize(Decimal("0.0001"))
    assert level_618.availability_mask[-1]

    # 50% retracement
    expected_50 = Decimal("18") - (Decimal("18") - Decimal("9")) * Decimal("0.5")
    assert level_50.values[-1] == expected_50
    assert level_50.availability_mask[-1]


def test_fib_retracement_up_levels():
    highs = _series([16, 18, 17, 16, 15, 14, 13, 12, 13, 14])
    lows = _series([14, 15, 14, 13, 12, 11, 10, 9, 10, 11])
    ctx = SeriesContext(high=highs, low=lows)

    result = fib_retracement(ctx, left=1, right=1, levels=(0.382,), mode="up")

    up = result["up"]["0.382"]

    assert up.availability_mask[-1]
    # Expected: move down from high=18 (idx=1) to low=9 (idx=7); low occurs after high
    expected = Decimal("9") + (Decimal("18") - Decimal("9")) * Decimal("0.382")
    assert up.values[-1].quantize(Decimal("0.0001")) == expected.quantize(Decimal("0.0001"))


def test_fib_retracement_insufficient_swings():
    highs = _series([10, 11, 12])
    lows = _series([9, 10, 11])
    ctx = SeriesContext(high=highs, low=lows)

    result = fib_retracement(ctx, left=2, right=2)

    anchor_high = result["anchor_high"]
    anchor_low = result["anchor_low"]

    assert all(not flag for flag in anchor_high.availability_mask)
    assert all(not flag for flag in anchor_low.availability_mask)
    assert result["down"] == {} or all(not series.availability_mask[-1] for series in result["down"].values())


def test_fib_level_helpers_return_single_series():
    highs = _series([10, 12, 15, 12, 11, 16, 18, 17, 16])
    lows = _series([8, 9, 11, 10, 9, 12, 14, 13, 12])
    ctx = SeriesContext(high=highs, low=lows)

    level_down = fib_level_down(ctx, left=1, right=1, level=0.618)
    level_up = fib_level_up(ctx, left=1, right=1, level=0.382)
    anchor_high = fib_anchor_high(ctx, left=1, right=1)
    anchor_low = fib_anchor_low(ctx, left=1, right=1)

    assert level_down.availability_mask[-1]
    assert all(isinstance(v, Decimal) for v in level_down.values)
    assert all(isinstance(v, Decimal) for v in level_up.values)
    assert anchor_high.values[-1] == Decimal("18")
    assert anchor_low.values[-1] == Decimal("9")


def test_fib_level_down_supports_leg_index():
    highs = _series([10, 13, 11, 15, 12, 17, 13, 16, 12])
    lows = _series([9, 10, 7, 11, 8, 12, 9, 11, 8])
    ctx = SeriesContext(high=highs, low=lows)

    latest_leg = fib_level_down(ctx, left=1, right=1, level=0.618, leg=1)
    previous_leg = fib_level_down(ctx, left=1, right=1, level=0.618, leg=2)

    assert latest_leg.availability_mask[-1]
    assert previous_leg.availability_mask[-1]
    assert latest_leg.values[-1] != previous_leg.values[-1]


def test_fib_pairing_mode_latest_valid_can_keep_more_legs():
    highs = _series([10, 13, 12, 15, 14, 16, 15, 14])
    lows = _series([9, 10, 7, 9, 9, 9, 10, 11])
    ctx = SeriesContext(high=highs, low=lows)

    strict = fib_level_down(ctx, left=1, right=1, level=0.5, leg=2, pairing_mode="strict_alternating")
    latest = fib_level_down(ctx, left=1, right=1, level=0.5, leg=2, pairing_mode="latest_valid")

    assert not strict.availability_mask[-1]
    assert latest.availability_mask[-1]


def test_fib_max_leg_age_bars_invalidates_old_legs():
    highs = _series([10, 13, 11, 15, 12, 17, 13, 16, 12])
    lows = _series([9, 10, 7, 11, 8, 12, 9, 11, 8])
    ctx = SeriesContext(high=highs, low=lows)

    series = fib_level_down(ctx, left=1, right=1, level=0.5, max_leg_age_bars=0)

    assert not series.availability_mask[7]
    assert series.availability_mask[8]


def test_fib_min_leg_size_filter():
    highs = _series([100, 101, 100.5, 102, 101.5, 102.5, 101.8])
    lows = _series([99.5, 99.8, 99, 100, 99.9, 100.2, 100.0])
    ctx = SeriesContext(high=highs, low=lows)

    series = fib_level_down(ctx, left=1, right=1, level=0.5, min_leg_size_pct=20)
    assert all(not available for available in series.availability_mask)


def test_fib_invalid_params():
    highs = _series([10, 12, 11, 13, 12])
    lows = _series([9, 10, 8, 11, 9])
    ctx = SeriesContext(high=highs, low=lows)

    with pytest.raises(ValueError):
        fib_level_down(ctx, left=1, right=1, leg=0)

    with pytest.raises(ValueError):
        fib_level_down(ctx, left=1, right=1, pairing_mode="unknown")  # type: ignore[arg-type]


def test_fib_levels_respect_right_bar_confirmation_no_lookahead():
    highs = _series([10, 12, 15, 14, 13, 16, 18, 17, 16, 15])
    lows = _series([8, 9, 11, 10, 9, 12, 14, 13, 12, 11])
    ctx = SeriesContext(high=highs, low=lows)

    # With right=2:
    # low pivot idx=4 -> confirms at 6
    # high pivot idx=6 -> confirms at 8
    # so the down leg becomes visible at idx=8.
    series = fib_level_down(ctx, left=1, right=2, level=0.5, leg=1)
    assert not series.availability_mask[7]
    assert series.availability_mask[8]
