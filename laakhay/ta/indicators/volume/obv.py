"""On-Balance Volume (OBV) indicator."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ...core import Series
from ...core.types import Price, Qty
from ...registry.registry import register
from ...registry.models import SeriesContext


@register("obv", description="On-Balance Volume indicator")
def obv(ctx: SeriesContext) -> Series[Qty]:
    """
    On-Balance Volume indicator.
    
    Calculates cumulative volume based on price direction:
    - If close > previous close: add volume
    - If close < previous close: subtract volume
    - If close = previous close: add zero
    """
    # Get required series
    if not hasattr(ctx, 'close') or not hasattr(ctx, 'volume'):
        raise ValueError("OBV requires both 'close' and 'volume' series in context")
    
    close_series = ctx.close
    volume_series = ctx.volume
    
    if len(close_series) != len(volume_series):
        raise ValueError("Close and volume series must have the same length")
    
    n = len(close_series)
    if n == 0:
        return Series[Qty](timestamps=(), values=(), symbol=close_series.symbol, timeframe=close_series.timeframe)
    
    obv_values: list[Qty] = []
    obv_stamps: list[Any] = []
    
    # Start with first volume value
    obv_values.append(Qty(volume_series.values[0]))
    obv_stamps.append(close_series.timestamps[0])
    
    # Calculate OBV for remaining values
    for i in range(1, n):
        prev_close = Decimal(str(close_series.values[i-1]))
        curr_close = Decimal(str(close_series.values[i]))
        curr_volume = Decimal(str(volume_series.values[i]))
        
        prev_obv = Decimal(str(obv_values[-1]))
        
        if curr_close > prev_close:
            # Price up: add volume
            new_obv = prev_obv + curr_volume
        elif curr_close < prev_close:
            # Price down: subtract volume
            new_obv = prev_obv - curr_volume
        else:
            # Price unchanged: add zero
            new_obv = prev_obv
        
        obv_values.append(Qty(new_obv))
        obv_stamps.append(close_series.timestamps[i])
    
    return Series[Qty](
        timestamps=tuple(obv_stamps),
        values=tuple(obv_values),
        symbol=close_series.symbol,
        timeframe=close_series.timeframe,
    )
