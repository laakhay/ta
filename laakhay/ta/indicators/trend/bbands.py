"""Bollinger Bands indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...primitives import rolling_mean, rolling_std  # type: ignore
from .. import Expression, Literal, Price, SeriesContext, register


@register("bbands", description="Bollinger Bands with upper, middle, and lower bands")
def bbands(
    ctx: SeriesContext, period: int = 20, std_dev: float = 2.0
) -> tuple[Series[Price], Series[Price], Series[Price]]:
    """
    Bollinger Bands indicator using primitives.

    Returns (upper_band, middle_band, lower_band) where:
    - middle_band = SMA(period)
    - upper_band = middle_band + (std_dev * standard_deviation)
    - lower_band = middle_band - (std_dev * standard_deviation)
    """
    if period <= 0 or std_dev <= 0:
        raise ValueError("Bollinger Bands period and std_dev must be positive")

    close = ctx.close
    if close is None or len(close) < period:
        empty = close.__class__(timestamps=(), values=(), symbol=close.symbol, timeframe=close.timeframe)
        return empty, empty, empty

    # Calculate middle band and standard deviation
    middle_band = rolling_mean(ctx, period)  # type: ignore
    std_deviation = rolling_std(ctx, period)  # type: ignore

    # Calculate upper and lower bands using expressions
    middle_expr = Expression(Literal(middle_band))  # type: ignore
    std_expr = Expression(Literal(std_deviation))  # type: ignore

    upper_band = (middle_expr + (std_expr * std_dev)).evaluate({})  # type: ignore
    lower_band = (middle_expr - (std_expr * std_dev)).evaluate({})  # type: ignore

    return upper_band, middle_band, lower_band  # type: ignore
