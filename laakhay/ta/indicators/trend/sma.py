"""Simple Moving Average (SMA) indicator and utilities."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ...core import Series
from ...core.types import Price
from ...registry.registry import register
from ...registry.models import SeriesContext


def _select_source_series(ctx: SeriesContext) -> Series[Price]:
    """Pick a reasonable default source series from the context."""
    names = ctx.available_series
    for candidate in ("price", "close"):
        if candidate in names:
            return getattr(ctx, candidate)
    if not names:
        raise ValueError("SeriesContext has no series to operate on")
    return getattr(ctx, names[0])


def calculate_sma(series: Series[Price], period: int) -> Series[Price]:
    """
    Calculate Simple Moving Average for a series.
    
    This is a pure function that can be reused across indicators.
    """
    if period <= 0:
        raise ValueError("SMA period must be positive")
    
    n = len(series)
    if n == 0:
        return Series[Price](timestamps=(), values=(), symbol=series.symbol, timeframe=series.timeframe)
    if n < period:
        return Series[Price](timestamps=(), values=(), symbol=series.symbol, timeframe=series.timeframe)
    
    values: list[Price] = []
    stamps: list[Any] = []
    
    for i in range(period - 1, n):
        window_sum = Decimal('0')
        for j in range(i - period + 1, i + 1):
            window_sum += Decimal(str(series.values[j]))
        avg = window_sum / Decimal(str(period))
        values.append(Price(avg))
        stamps.append(series.timestamps[i])
    
    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=series.symbol,
        timeframe=series.timeframe,
    )


@register("sma", description="Simple Moving Average over a price series")
def sma(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """
    Simple Moving Average.
    
    Produces an SMA of the selected source series (defaults to 'price' or
    'close'), returning a shorter series that starts at index (period-1).
    """
    source = _select_source_series(ctx)
    return calculate_sma(source, period)
