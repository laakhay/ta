"""Simple Moving Average (SMA) indicator using primitives."""

from __future__ import annotations

from ...primitives import _select_field
from .. import Price, Series, SeriesContext, register, rolling_mean


@register("sma", description="Simple Moving Average over a price series")
def sma(ctx: SeriesContext, period: int = 20, source: str | None = None) -> Series[Price]:
    """
    Simple Moving Average using rolling_mean primitive.

    This implementation uses the rolling_mean primitive instead of custom code,
    making it more consistent and maintainable.

    Args:
        ctx: Series context containing price/volume data
        period: Number of periods for the moving average
        source: Optional field name to use as source (e.g., 'close', 'volume', 'high', 'low', 'open').
                Defaults to 'close' or 'price' if not specified.
    """
    if source:
        selected_series = _select_field(ctx, source)
        # Create a new context with the selected series as 'price' for rolling_mean
        new_ctx = SeriesContext(price=selected_series)
        return rolling_mean(new_ctx, period)
    return rolling_mean(ctx, period)
