"""Tests for fib_retracement indicator."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.pattern import fib_retracement
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
    highs = _series([18, 17, 16, 15, 14, 13, 12, 13, 14])
    lows = _series([16, 15, 14, 13, 12, 11, 10, 11, 12])
    ctx = SeriesContext(high=highs, low=lows)

    result = fib_retracement(ctx, left=1, right=1, levels=(0.382,), mode="up")

    up = result["up"]["0.382"]

    assert up.availability_mask[-1]
    # Expected: move down from high=18 (idx=0) to low=10 (idx=6); low occurs after high
    expected = Decimal("10") + (Decimal("18") - Decimal("10")) * Decimal("0.382")
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
