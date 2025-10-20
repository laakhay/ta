"""Relative Strength Index (RSI) indicator."""

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


@register("rsi", description="Relative Strength Index")
def rsi(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Relative Strength Index indicator.
    
    Calculates RSI using smoothed gains and losses over the specified period.
    RSI ranges from 0 to 100, with values above 70 typically indicating
    overbought conditions and values below 30 indicating oversold conditions.
    """
    if period <= 0:
        raise ValueError("RSI period must be positive")
    
    source = _select_source_series(ctx)
    n = len(source)
    if n == 0:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)
    if n < 2:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)
    
    # Calculate price changes
    changes: list[Decimal] = []
    for i in range(1, n):
        prev_price = Decimal(str(source.values[i-1]))
        curr_price = Decimal(str(source.values[i]))
        change = curr_price - prev_price
        changes.append(change)
    
    if len(changes) < period:
        return Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)
    
    # Calculate gains and losses
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    
    for change in changes:
        if change > 0:
            gains.append(change)
            losses.append(Decimal('0'))
        else:
            gains.append(Decimal('0'))
            losses.append(-change)  # Losses are positive values
    
    # Calculate initial average gain and loss
    initial_gain_sum = sum(gains[:period])
    initial_loss_sum = sum(losses[:period])
    avg_gain = initial_gain_sum / Decimal(str(period))
    avg_loss = initial_loss_sum / Decimal(str(period))
    
    rsi_values: list[Price] = []
    rsi_stamps: list[Any] = []
    
    # Calculate RSI for the first period
    if avg_loss == 0:
        rsi_value = Decimal('100')
    else:
        rs = avg_gain / avg_loss
        rsi_value = Decimal('100') - (Decimal('100') / (Decimal('1') + rs))
    
    rsi_values.append(Price(rsi_value))
    rsi_stamps.append(source.timestamps[period])
    
    # Calculate RSI for remaining periods using Wilder's smoothing
    for i in range(period, len(changes)):
        # Update average gain and loss using Wilder's smoothing
        avg_gain = (avg_gain * Decimal(str(period - 1)) + gains[i]) / Decimal(str(period))
        avg_loss = (avg_loss * Decimal(str(period - 1)) + losses[i]) / Decimal(str(period))
        
        # Calculate RSI
        if avg_loss == 0:
            rsi_value = Decimal('100')
        else:
            rs = avg_gain / avg_loss
            rsi_value = Decimal('100') - (Decimal('100') / (Decimal('1') + rs))
        
        rsi_values.append(Price(rsi_value))
        rsi_stamps.append(source.timestamps[i + 1])
    
    return Series[Price](
        timestamps=tuple(rsi_stamps),
        values=tuple(rsi_values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )
