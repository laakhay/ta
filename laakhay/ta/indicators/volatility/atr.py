"""Average True Range (ATR) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...core.types import Price
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...primitives import true_range, rolling_mean


@register("atr", description="Average True Range indicator")
def atr(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Average True Range indicator using primitives.
    
    ATR = Rolling Mean of True Range
    """
    if period <= 0:
        raise ValueError("ATR period must be positive")

    # Validate series lengths before processing
    required_series = ['high', 'low', 'close']
    series_lengths = []
    for s in required_series:
        if hasattr(ctx, s) and getattr(ctx, s) is not None:
            series_lengths.append(len(getattr(ctx, s)))
    
    if len(series_lengths) > 1 and len(set(series_lengths)) > 1:
        raise ValueError("All series must have the same length")

    # Calculate True Range using primitive
    tr_series = true_range(ctx)
    
    # Calculate ATR as rolling mean of True Range
    tr_ctx = SeriesContext(close=tr_series)
    return rolling_mean(tr_ctx, period)
