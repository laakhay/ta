"""Core technical indicators.

This module contains basic indicator implementations registered with the
global registry for immediate use by clients and higher-level pipelines.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..core import Series
from ..core.types import Price
from ..registry.registry import register
from ..registry.models import SeriesContext


def _select_source_series(ctx: SeriesContext) -> Series[Price]:
    """Pick a reasonable default source series from the context.

    Preference order: 'price', 'close', first available series.
    """
    names = ctx.available_series
    for candidate in ("price", "close"):
        if candidate in names:
            return getattr(ctx, candidate)
    if not names:
        raise ValueError("SeriesContext has no series to operate on")
    return getattr(ctx, names[0])


@register("sma", description="Simple Moving Average over a price series")
def sma(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """
    Simple Moving Average.

    Produces an SMA of the selected source series (defaults to 'price' or
    'close'), returning a shorter series that starts at index (period-1).
    """
    if period <= 0:
        raise ValueError("SMA period must be positive")

    source = _select_source_series(ctx)
    n = len(source)
    if n == 0:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)
    if n < period:
        # Not enough data; return empty result with consistent metadata
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)

    # Compute rolling sums using a simple sliding window for clarity
    window_sum = Decimal(0)
    values: list[Price] = []
    stamps: list[Any] = []

    # Prime the first window
    for i in range(period):
        window_sum += Decimal(str(source.values[i]))

    avg = window_sum / Decimal(period)
    values.append(Price(avg))
    stamps.append(source.timestamps[period - 1])

    # Slide the window
    for i in range(period, n):
        window_sum += Decimal(str(source.values[i]))
        window_sum -= Decimal(str(source.values[i - period]))
        avg = window_sum / Decimal(period)
        values.append(Price(avg))
        stamps.append(source.timestamps[i])

    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )
