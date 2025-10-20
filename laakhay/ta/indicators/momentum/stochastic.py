"""Stochastic Oscillator indicator."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Tuple

from ...core import Series
from ...core.types import Price
from ...registry.registry import register
from ...registry.models import SeriesContext


@register("stochastic", description="Stochastic Oscillator (%K and %D)")
def stochastic(
    ctx: SeriesContext, 
    k_period: int = 14, 
    d_period: int = 3
) -> Tuple[Series[Price], Series[Price]]:
    """
    Stochastic Oscillator indicator.
    
    Returns (%K, %D) where:
    - %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
    - %D = Simple Moving Average of %K
    
    Requires high, low, and close series.
    """
    if k_period <= 0 or d_period <= 0:
        raise ValueError("Stochastic periods must be positive")
    
    # Get required series
    required_series = ['high', 'low', 'close']
    missing = [s for s in required_series if not hasattr(ctx, s)]
    if missing:
        raise ValueError(f"Stochastic requires series: {required_series}, missing: {missing}")
    
    high_series = ctx.high
    low_series = ctx.low
    close_series = ctx.close
    
    # Validate series lengths
    series_lengths = [len(high_series), len(low_series), len(close_series)]
    if len(set(series_lengths)) > 1:
        raise ValueError("All series must have the same length")
    
    n = len(close_series)
    if n == 0:
        empty = Series[Price](timestamps=(), values=(), symbol=close_series.symbol, timeframe=close_series.timeframe)
        return empty, empty
    if n < k_period:
        empty = Series[Price](timestamps=(), values=(), symbol=close_series.symbol, timeframe=close_series.timeframe)
        return empty, empty
    
    # Calculate %K values
    k_values: list[Price] = []
    k_stamps: list[Any] = []
    
    for i in range(k_period - 1, n):
        # Find highest high and lowest low in the period
        period_highs = [Decimal(str(high_series.values[j])) for j in range(i - k_period + 1, i + 1)]
        period_lows = [Decimal(str(low_series.values[j])) for j in range(i - k_period + 1, i + 1)]
        
        highest_high = max(period_highs)
        lowest_low = min(period_lows)
        current_close = Decimal(str(close_series.values[i]))
        
        # Calculate %K
        if highest_high == lowest_low:
            # Avoid division by zero
            k_value = Decimal('50')  # Neutral value
        else:
            k_value = ((current_close - lowest_low) / (highest_high - lowest_low)) * Decimal('100')
        
        k_values.append(Price(k_value))
        k_stamps.append(close_series.timestamps[i])
    
    k_series = Series[Price](
        timestamps=tuple(k_stamps),
        values=tuple(k_values),
        symbol=close_series.symbol,
        timeframe=close_series.timeframe,
    )
    
    # Calculate %D (SMA of %K)
    if len(k_series) < d_period:
        empty = Series[Price](timestamps=(), values=(), symbol=close_series.symbol, timeframe=close_series.timeframe)
        return k_series, empty
    
    d_values: list[Price] = []
    d_stamps: list[Any] = []
    
    for i in range(d_period - 1, len(k_series)):
        window_sum = Decimal('0')
        for j in range(i - d_period + 1, i + 1):
            window_sum += Decimal(str(k_series.values[j]))
        d_value = window_sum / Decimal(str(d_period))
        d_values.append(Price(d_value))
        d_stamps.append(k_series.timestamps[i])
    
    d_series = Series[Price](
        timestamps=tuple(d_stamps),
        values=tuple(d_values),
        symbol=close_series.symbol,
        timeframe=close_series.timeframe,
    )
    
    return k_series, d_series
