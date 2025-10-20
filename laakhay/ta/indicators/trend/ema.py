"""Exponential Moving Average (EMA) indicator."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ...core import Series
from ...core.types import Price
from ...registry.registry import register
from ...registry.models import SeriesContext
from ..utils import _select_source_series


@register("ema", description="Exponential Moving Average over a price series")
def ema(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """
    Exponential Moving Average.
    
    Produces an EMA of the selected source series (defaults to 'price' or
    'close'), returning a series of the same length as input.
    """
    if period <= 0:
        raise ValueError("EMA period must be positive")
    
    source = _select_source_series(ctx)
    n = len(source)
    if n == 0:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)
    
    # Calculate smoothing factor
    alpha = Decimal('2') / Decimal(str(period + 1))
    
    # Initialize with first value
    values: list[Price] = [Price(source.values[0])]
    stamps: list[Any] = [source.timestamps[0]]
    
    # Calculate EMA for remaining values
    for i in range(1, n):
        prev_ema = values[-1]
        current_price = Decimal(str(source.values[i]))
        ema_value = alpha * current_price + (Decimal('1') - alpha) * prev_ema
        values.append(Price(ema_value))
        stamps.append(source.timestamps[i])
    
    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )
