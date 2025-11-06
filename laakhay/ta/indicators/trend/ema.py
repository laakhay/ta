"""Exponential Moving Average (EMA) indicator using primitives."""

from __future__ import annotations

from .. import register, SeriesContext, Price
from ...primitives import rolling_ema  # type: ignore
from ...core import Series


@register("ema", description="Exponential Moving Average over a price series")
def ema(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """
    Exponential Moving Average using rolling_ema primitive.
    
    This implementation uses the rolling_ema primitive for consistency
    and maintainability.
    """
    return rolling_ema(ctx, period)  # type: ignore
