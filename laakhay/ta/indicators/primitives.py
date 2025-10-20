"""Primitive operations for building indicators using expressions.

This module provides low-level operations that can be composed using
the expression system to create complex indicators.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..core import Series
from ..core.types import Price
from ..registry.models import SeriesContext
from ..registry.registry import register


def _select_source_series(ctx: SeriesContext) -> Series[Price]:
    """Pick a reasonable default source series from the context."""
    names = ctx.available_series
    for candidate in ("price", "close"):
        if candidate in names:
            return getattr(ctx, candidate)
    if not names:
        raise ValueError("SeriesContext has no series to operate on")
    return getattr(ctx, names[0])


@register("rolling_sum", description="Rolling sum over a window")
def rolling_sum(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """Calculate rolling sum over a window."""
    source = _select_source_series(ctx)

    if period <= 0:
        raise ValueError("Period must be positive")

    n = len(source)
    if n == 0 or n < period:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(period - 1, n):
        window_sum = Decimal('0')
        for j in range(i - period + 1, i + 1):
            window_sum += Decimal(str(source.values[j]))
        values.append(Price(window_sum))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("rolling_mean", description="Rolling mean over a window")
def rolling_mean(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """Calculate rolling mean over a window."""
    source = _select_source_series(ctx)

    if period <= 0:
        raise ValueError("Period must be positive")

    n = len(source)
    if n == 0 or n < period:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(period - 1, n):
        window_sum = Decimal('0')
        for j in range(i - period + 1, i + 1):
            window_sum += Decimal(str(source.values[j]))
        avg = window_sum / Decimal(str(period))
        values.append(Price(avg))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("shift", description="Shift series by n periods")
def shift(ctx: SeriesContext, periods: int = 1) -> Series[Price]:
    """Shift series by n periods (positive = forward, negative = backward)."""
    source = _select_source_series(ctx)

    n = len(source)
    if n == 0:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

    if periods == 0:
        return source

    if periods > 0:
        # Forward shift: pad with None/NaN at the beginning
        # For now, we'll just return a shorter series
        if periods >= n:
            return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

        return Series[Price](
            timestamps=source.timestamps[periods:],
            values=source.values[periods:],
            symbol=source.symbol,
            timeframe=source.timeframe,
        )
    else:
        # Backward shift: pad at the end
        periods = abs(periods)
        if periods >= n:
            return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

        return Series[Price](
            timestamps=source.timestamps[:-periods],
            values=source.values[:-periods],
            symbol=source.symbol,
            timeframe=source.timeframe,
        )


@register("diff", description="Difference between consecutive values")
def diff(ctx: SeriesContext) -> Series[Price]:
    """Calculate difference between consecutive values."""
    source = _select_source_series(ctx)

    n = len(source)
    if n < 2:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(1, n):
        diff_val = Decimal(str(source.values[i])) - Decimal(str(source.values[i-1]))
        values.append(Price(diff_val))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("max", description="Maximum value in a rolling window")
def rolling_max(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """Calculate rolling maximum over a window."""
    source = _select_source_series(ctx)

    if period <= 0:
        raise ValueError("Period must be positive")

    n = len(source)
    if n == 0 or n < period:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(period - 1, n):
        window_max = max(Decimal(str(source.values[j])) for j in range(i - period + 1, i + 1))
        values.append(Price(window_max))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("min", description="Minimum value in a rolling window")
def rolling_min(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """Calculate rolling minimum over a window."""
    source = _select_source_series(ctx)

    if period <= 0:
        raise ValueError("Period must be positive")

    n = len(source)
    if n == 0 or n < period:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(period - 1, n):
        window_min = min(Decimal(str(source.values[j])) for j in range(i - period + 1, i + 1))
        values.append(Price(window_min))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("rolling_std", description="Rolling standard deviation over a window")
def rolling_std(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """Calculate rolling standard deviation over a window."""
    source = _select_source_series(ctx)

    if period <= 0:
        raise ValueError("Period must be positive")

    n = len(source)
    if n == 0 or n < period:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(period - 1, n):
        # Get window values
        window_values = [Decimal(str(source.values[j])) for j in range(i - period + 1, i + 1)]

        # Calculate mean
        mean = sum(window_values) / Decimal(str(period))

        # Calculate variance
        variance = sum((x - mean) ** 2 for x in window_values) / Decimal(str(period))

        # Calculate standard deviation
        std_dev = variance.sqrt()

        values.append(Price(std_dev))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("elementwise_max", description="Element-wise maximum of two series")
def elementwise_max(ctx: SeriesContext, other_series: Series[Price]) -> Series[Price]:
    """Calculate element-wise maximum of two series."""
    source = _select_source_series(ctx)

    if len(source) != len(other_series):
        raise ValueError("Series must have the same length for element-wise operations")

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(len(source)):
        max_val = max(Decimal(str(source.values[i])), Decimal(str(other_series.values[i])))
        values.append(Price(max_val))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("elementwise_min", description="Element-wise minimum of two series")
def elementwise_min(ctx: SeriesContext, other_series: Series[Price]) -> Series[Price]:
    """Calculate element-wise minimum of two series."""
    source = _select_source_series(ctx)

    if len(source) != len(other_series):
        raise ValueError("Series must have the same length for element-wise operations")

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(len(source)):
        min_val = min(Decimal(str(source.values[i])), Decimal(str(other_series.values[i])))
        values.append(Price(min_val))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("cumulative_sum", description="Cumulative sum of a series")
def cumulative_sum(ctx: SeriesContext) -> Series[Price]:
    """Calculate cumulative sum of a series."""
    source = _select_source_series(ctx)

    if len(source) == 0:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

    values: list[Price] = []
    stamps: list[Any] = []
    cumsum = Decimal('0')

    for i in range(len(source)):
        cumsum += Decimal(str(source.values[i]))
        values.append(Price(cumsum))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("positive_values", description="Extract positive values from a series")
def positive_values(ctx: SeriesContext) -> Series[Price]:
    """Extract only positive values from a series, zero for negative values."""
    source = _select_source_series(ctx)

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(len(source)):
        val = Decimal(str(source.values[i]))
        positive_val = max(val, Decimal('0'))
        values.append(Price(positive_val))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("negative_values", description="Extract negative values from a series")
def negative_values(ctx: SeriesContext) -> Series[Price]:
    """Extract only negative values from a series, zero for positive values."""
    source = _select_source_series(ctx)

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(len(source)):
        val = Decimal(str(source.values[i]))
        negative_val = min(val, Decimal('0'))
        values.append(Price(negative_val))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("rolling_ema", description="Exponential Moving Average over a window")
def rolling_ema(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """Calculate exponential moving average over a window."""
    source = _select_source_series(ctx)

    if period <= 0:
        raise ValueError("Period must be positive")

    n = len(source)
    if n == 0:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

    # Calculate smoothing factor
    multiplier = Decimal('2') / Decimal(str(period + 1))

    values: list[Price] = []
    stamps: list[Any] = []

    # Initialize EMA with first value
    ema_value = Decimal(str(source.values[0]))
    values.append(Price(ema_value))
    stamps.append(source.timestamps[0])

    # Calculate EMA for remaining values
    for i in range(1, n):
        current_price = Decimal(str(source.values[i]))
        # EMA = (Close * multiplier) + (Previous EMA * (1 - multiplier))
        ema_value = (current_price * multiplier) + (ema_value * (Decimal('1') - multiplier))
        values.append(Price(ema_value))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )


@register("true_range", description="True Range calculation for ATR")
def true_range(ctx: SeriesContext) -> Series[Price]:
    """Calculate True Range for ATR indicator."""
    required_series = ['high', 'low', 'close']
    missing = [s for s in required_series if not hasattr(ctx, s)]
    if missing:
        raise ValueError(f"True Range requires series: {required_series}, missing: {missing}")

    high_series = ctx.high
    low_series = ctx.low
    close_series = ctx.close

    if len(close_series) == 0:
        return Series[Price](timestamps=(), values=(), symbol=close_series.symbol, timeframe=close_series.timeframe)

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(len(close_series)):
        if i == 0:
            # First bar: TR = high - low
            tr = Decimal(str(high_series.values[i])) - Decimal(str(low_series.values[i]))
        else:
            # Subsequent bars: TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
            high_low = Decimal(str(high_series.values[i])) - Decimal(str(low_series.values[i]))
            high_prev_close = abs(Decimal(str(high_series.values[i])) - Decimal(str(close_series.values[i-1])))
            low_prev_close = abs(Decimal(str(low_series.values[i])) - Decimal(str(close_series.values[i-1])))
            tr = max(high_low, high_prev_close, low_prev_close)

        values.append(Price(tr))
        stamps.append(close_series.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=close_series.symbol,
        timeframe=close_series.timeframe,
    )


@register("typical_price", description="Typical Price (HLC/3)")
def typical_price(ctx: SeriesContext) -> Series[Price]:
    """Calculate typical price (High + Low + Close) / 3."""
    required_series = ['high', 'low', 'close']
    missing = [s for s in required_series if not hasattr(ctx, s)]
    if missing:
        raise ValueError(f"Typical Price requires series: {required_series}, missing: {missing}")

    high_series = ctx.high
    low_series = ctx.low
    close_series = ctx.close

    if len(close_series) == 0:
        return Series[Price](timestamps=(), values=(), symbol=close_series.symbol, timeframe=close_series.timeframe)

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(len(close_series)):
        typical = (Decimal(str(high_series.values[i])) + 
                  Decimal(str(low_series.values[i])) + 
                  Decimal(str(close_series.values[i]))) / Decimal('3')
        values.append(Price(typical))
        stamps.append(close_series.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=close_series.symbol,
        timeframe=close_series.timeframe,
    )


@register("sign", description="Sign function for price changes")
def sign(ctx: SeriesContext) -> Series[Price]:
    """Return sign of price changes: +1 for positive, -1 for negative, 0 for zero."""
    source = _select_source_series(ctx)

    if len(source) < 2:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

    values: list[Price] = []
    stamps: list[Any] = []

    for i in range(1, len(source)):
        current = Decimal(str(source.values[i]))
        previous = Decimal(str(source.values[i-1]))
        change = current - previous

        if change > 0:
            sign_val = Decimal('1')
        elif change < 0:
            sign_val = Decimal('-1')
        else:
            sign_val = Decimal('0')

        values.append(Price(sign_val))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )
