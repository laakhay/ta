"""Tests for additional primitives added in Commit 9b."""

from datetime import timezone, datetime, timedelta
UTC = timezone.utc
from decimal import Decimal

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.primitives import (
    cumulative_sum,
    negative_values,
    positive_values,
    rolling_rma,
    true_range,
)
from laakhay.ta.registry.models import SeriesContext


def _make_series(values: list[int | float | Decimal], symbol: str = "BTCUSDT", timeframe: str = "1h") -> Series[Price]:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = tuple(base + timedelta(hours=i) for i in range(len(values)))
    price_values = tuple(Decimal(str(v)) for v in values)
    return Series[Price](timestamps=timestamps, values=price_values, symbol=symbol, timeframe=timeframe)


def test_rolling_rma_basic():
    # RSI example often uses 14, but let's use small period for manual verification
    # Period = 2. Alpha = 1/2 = 0.5.
    # Values: [10, 20, 10, 20]
    # RMA[0] = 10 (seed)
    # RMA[1] = 0.5 * 20 + 0.5 * 10 = 15
    # RMA[2] = 0.5 * 10 + 0.5 * 15 = 5 + 7.5 = 12.5
    # RMA[3] = 0.5 * 20 + 0.5 * 12.5 = 10 + 6.25 = 16.25

    close = _make_series([10, 20, 10, 20])
    ctx = SeriesContext(close=close)

    result = rolling_rma(ctx, period=2)

    expected = [
        Decimal("10"),
        Decimal("15"),
        Decimal("12.5"),
        Decimal("16.25"),
    ]

    assert len(result) == 4
    for r, e in zip(result.values, expected, strict=True):
        assert abs(r - e) < Decimal("0.0001")


def test_positive_values():
    vals = _make_series([10, -5, 20, -1, 0])
    ctx = SeriesContext(close=vals)

    result = positive_values(ctx)

    expected = [
        Decimal("10"),
        Decimal("0"),
        Decimal("20"),
        Decimal("0"),
        Decimal("0"),
    ]
    assert tuple(result.values) == tuple(expected)


def test_negative_values():
    vals = _make_series([10, -5, 20, -1, 0])
    ctx = SeriesContext(close=vals)

    result = negative_values(ctx)

    expected = [
        Decimal("0"),
        Decimal("-5"),
        Decimal("0"),
        Decimal("-1"),
        Decimal("0"),
    ]
    assert tuple(result.values) == tuple(expected)


def test_cumulative_sum():
    vals = _make_series([1, 2, 3, 4])
    ctx = SeriesContext(close=vals)

    result = cumulative_sum(ctx)

    expected = [
        Decimal("1"),
        Decimal("3"),
        Decimal("6"),
        Decimal("10"),
    ]
    assert tuple(result.values) == tuple(expected)


def test_true_range_calculation():
    # High, Low, Close
    # Bar 0: H=10, L=5, C=8. TR = H-L = 5
    # Bar 1: H=12, L=9, C=10. PrevC=8.
    #   H-L = 3
    #   |H-PrevC| = |12-8| = 4
    #   |L-PrevC| = |9-8| = 1
    #   TR = 4
    # Bar 2: H=11, L=10, C=10.5. PrevC=10.
    #   H-L = 1
    #   |H-PrevC| = |11-10| = 1
    #   |L-PrevC| = |10-10| = 0
    #   TR = 1

    high = _make_series([10, 12, 11])
    low = _make_series([5, 9, 10])
    close = _make_series([8, 10, 10.5])

    ctx = SeriesContext(high=high, low=low, close=close)

    result = true_range(ctx)

    expected = [
        Decimal("5"),
        Decimal("4"),
        Decimal("1"),
    ]
    assert tuple(result.values) == tuple(expected)
