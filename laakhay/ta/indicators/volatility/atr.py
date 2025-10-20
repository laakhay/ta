"""Average True Range (ATR) indicator."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ...core import Series
from ...core.types import Price
from ...registry.registry import register
from ...registry.models import SeriesContext


@register("atr", description="Average True Range indicator")
def atr(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Average True Range indicator.
    
    Calculates ATR using true range values smoothed by a moving average.
    Requires high, low, and close series.
    """
    if period <= 0:
        raise ValueError("ATR period must be positive")
    
    # Get required series
    required_series = ['high', 'low', 'close']
    missing = [s for s in required_series if not hasattr(ctx, s)]
    if missing:
        raise ValueError(f"ATR requires series: {required_series}, missing: {missing}")
    
    high_series = ctx.high
    low_series = ctx.low
    close_series = ctx.close
    
    # Validate series lengths
    series_lengths = [len(high_series), len(low_series), len(close_series)]
    if len(set(series_lengths)) > 1:
        raise ValueError("All series must have the same length")
    
    n = len(close_series)
    if n == 0:
        return Series[Price](timestamps=(), values=(), symbol=close_series.symbol, timeframe=close_series.timeframe)
    if n < 2:
        # Need at least 2 values for true range calculation
        return Series[Price](timestamps=(), values=(), symbol=close_series.symbol, timeframe=close_series.timeframe)
    
    # Calculate true range for each period
    true_ranges: list[Price] = []
    
    for i in range(n):
        high_price = Decimal(str(high_series.values[i]))
        low_price = Decimal(str(low_series.values[i]))
        close_price = Decimal(str(close_series.values[i]))
        
        if i == 0:
            # First period: true range = high - low
            true_range = high_price - low_price
        else:
            # Subsequent periods: max of three values
            prev_close = Decimal(str(close_series.values[i-1]))
            tr1 = high_price - low_price
            tr2 = abs(high_price - prev_close)
            tr3 = abs(low_price - prev_close)
            true_range = max(tr1, tr2, tr3)
        
        true_ranges.append(Price(true_range))
    
    # Calculate ATR using simple moving average of true ranges
    if n < period:
        return Series[Price](timestamps=(), values=(), symbol=close_series.symbol, timeframe=close_series.timeframe)
    
    atr_values: list[Price] = []
    atr_stamps: list[Any] = []
    
    # Calculate ATR for each window
    for i in range(period - 1, n):
        window_sum = Decimal('0')
        for j in range(i - period + 1, i + 1):
            window_sum += Decimal(str(true_ranges[j]))
        atr_value = window_sum / Decimal(str(period))
        atr_values.append(Price(atr_value))
        atr_stamps.append(close_series.timestamps[i])
    
    return Series[Price](
        timestamps=tuple(atr_stamps),
        values=tuple(atr_values),
        symbol=close_series.symbol,
        timeframe=close_series.timeframe,
    )
