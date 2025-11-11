"""Exponential Moving Average (EMA) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...primitives import _select_field, rolling_ema  # type: ignore
from .. import Price, SeriesContext, register


@register("ema", description="Exponential Moving Average over a price series")
def ema(ctx: SeriesContext, period: int = 20, source: str | None = None) -> Series[Price]:
    """
    Exponential Moving Average using rolling_ema primitive.

    This implementation uses the rolling_ema primitive for consistency
    and maintainability.

    Args:
        ctx: Series context containing price/volume data
        period: Number of periods for the moving average
        source: Optional field name to use as source (e.g., 'close', 'volume', 'high', 'low', 'open').
                Defaults to 'close' or 'price' if not specified.
    """
    if source:
        selected_series = _select_field(ctx, source)
        # Create a new context with the selected series as 'price' for rolling_ema
        new_ctx = SeriesContext(price=selected_series)
        return rolling_ema(new_ctx, period)  # type: ignore
    return rolling_ema(ctx, period)  # type: ignore
