"""Bollinger Bands indicator using primitives."""

from __future__ import annotations

from .. import register, SeriesContext, Price, Expression, Literal, rolling_mean, rolling_std


@register("bbands", description="Bollinger Bands with upper, middle, and lower bands")
def bbands(
    ctx: SeriesContext,
    period: int = 20,
    std_dev: float = 2.0
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

    # Calculate middle band and standard deviation
    middle_band = rolling_mean(ctx, period)
    std_deviation = rolling_std(ctx, period)

    # Calculate upper and lower bands using expressions
    middle_expr = Expression(Literal(middle_band))
    std_expr = Expression(Literal(std_deviation))
    
    upper_band = (middle_expr + (std_expr * std_dev)).evaluate({})
    lower_band = (middle_expr - (std_expr * std_dev)).evaluate({})

    return upper_band, middle_band, lower_band
