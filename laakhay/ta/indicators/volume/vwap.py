"""Volume Weighted Average Price (VWAP) indicator."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ...core import Series
from ...core.types import Price
from ...registry.registry import register
from ...registry.models import SeriesContext
from ...expressions.operators import Expression
from ...expressions.models import Literal
from ..utils import calculate_typical_price


@register("vwap", description="Volume Weighted Average Price")
def vwap(ctx: SeriesContext) -> Series[Price]:
    """
    Volume Weighted Average Price indicator.
    
    Calculates VWAP using typical price (HLC/3) weighted by volume.
    Requires high, low, close, and volume series.
    """
    # Get required series
    required_series = ['high', 'low', 'close', 'volume']
    missing = [s for s in required_series if not hasattr(ctx, s)]
    if missing:
        raise ValueError(f"VWAP requires series: {required_series}, missing: {missing}")
    
    high_series = ctx.high
    low_series = ctx.low
    close_series = ctx.close
    volume_series = ctx.volume
    
    # Validate series lengths
    series_lengths = [len(high_series), len(low_series), len(close_series), len(volume_series)]
    if len(set(series_lengths)) > 1:
        raise ValueError("All series must have the same length")
    
    n = len(close_series)
    if n == 0:
        return Series[Price](timestamps=(), values=(), symbol=close_series.symbol, timeframe=close_series.timeframe)
    
    # Use expression system to calculate typical price
    typical_price_series = calculate_typical_price(high_series, low_series, close_series)
    
    vwap_values: list[Price] = []
    vwap_stamps: list[Any] = []
    
    cumulative_volume = Decimal('0')
    cumulative_volume_price = Decimal('0')
    
    for i in range(n):
        # Get typical price from expression result
        typical_price = Decimal(str(typical_price_series.values[i]))
        
        # Get volume
        volume = Decimal(str(volume_series.values[i]))
        
        # Update cumulative values
        cumulative_volume += volume
        cumulative_volume_price += typical_price * volume
        
        # Calculate VWAP
        if cumulative_volume > 0:
            vwap_value = cumulative_volume_price / cumulative_volume
        else:
            vwap_value = typical_price  # Fallback to typical price if no volume
        
        vwap_values.append(Price(vwap_value))
        vwap_stamps.append(close_series.timestamps[i])
    
    return Series[Price](
        timestamps=tuple(vwap_stamps),
        values=tuple(vwap_values),
        symbol=close_series.symbol,
        timeframe=close_series.timeframe,
    )
