"""Tests for newly added rolling arg-extrema primitives and helpers."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.primitives import (
    rolling_argmax,
    rolling_argmin,
    select,
    downsample,
)
from laakhay.ta.registry.models import SeriesContext


def _make_series(
    values: list[int | float | Decimal], symbol: str = "BTCUSDT", timeframe: str = "1h"
) -> Series[Price]:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = tuple(base + timedelta(hours=i) for i in range(len(values)))
    price_values = tuple(Decimal(str(v)) for v in values)
    return Series[Price](
        timestamps=timestamps, values=price_values, symbol=symbol, timeframe=timeframe
    )


def test_rolling_argmax_offsets_basic():
    close_series = _make_series([1, 3, 2, 4, 3])
    ctx = SeriesContext(close=close_series)

    result = rolling_argmax(ctx, period=3)

    assert result.symbol == close_series.symbol
    assert result.timeframe == close_series.timeframe
    assert tuple(result.values) == (
        Decimal(1),
        Decimal(0),
        Decimal(1),
    )


def test_rolling_argmin_offsets_basic():
    close_series = _make_series([5, 3, 4, 2, 3])
    ctx = SeriesContext(close=close_series)

    result = rolling_argmin(ctx, period=3)

    assert tuple(result.values) == (
        Decimal(1),
        Decimal(0),
        Decimal(1),
    )


def test_rolling_argmax_uses_field_parameter():
    close_series = _make_series([1, 1, 1, 1])
    high_series = _make_series([10, 11, 9, 12])
    ctx = SeriesContext(close=close_series, high=high_series)

    result = rolling_argmax(ctx, period=2, field="high")

    assert tuple(result.values) == (
        Decimal(0),
        Decimal(1),
        Decimal(0),
    )


def test_select_returns_requested_field():
    close_series = _make_series([1, 2, 3])
    high_series = _make_series([2, 3, 4])
    ctx = SeriesContext(close=close_series, high=high_series)

    result = select(ctx, field="high")

    assert result is high_series


def test_downsample_timeframe_override_for_single_series():
    close_series = _make_series([1, 2, 3, 4], timeframe="1h")
    ctx = SeriesContext(close=close_series)

    result = downsample(ctx, factor=2, target_timeframe="2h")

    assert result.timeframe == "2h"
    assert len(result.values) == 2


def test_downsample_timeframe_override_for_ohlcv():
    open_series = _make_series([1, 2, 3, 4], timeframe="1h")
    high_series = _make_series([2, 3, 4, 5], timeframe="1h")
    low_series = _make_series([0, 1, 2, 3], timeframe="1h")
    close_series = _make_series([1.5, 2.5, 3.5, 4.5], timeframe="1h")
    volume_series = _make_series([100, 200, 150, 250], timeframe="1h")

    ctx = SeriesContext(
        open=open_series,
        high=high_series,
        low=low_series,
        close=close_series,
        volume=volume_series,
    )

    result = downsample(ctx, factor=2, target="ohlcv", target_timeframe="2h")

    assert isinstance(result, dict)
    assert {key for key in ("open", "high", "low", "close")} <= set(result.keys())
    assert all(series.timeframe == "2h" for series in result.values())
