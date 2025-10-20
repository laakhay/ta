"""Simple Moving Average (SMA) indicator using primitives."""

from __future__ import annotations

from .. import register, SeriesContext, Price, rolling_mean


@register("sma", description="Simple Moving Average over a price series")
def sma(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """
    Simple Moving Average using rolling_mean primitive.
    
    This implementation uses the rolling_mean primitive instead of custom code,
    making it more consistent and maintainable.
    """
    return rolling_mean(ctx, period)
