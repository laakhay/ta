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
    if period <= 0:
        raise ValueError("Bollinger Bands period must be positive")
    if std_dev <= 0:
        raise ValueError("Standard deviation multiplier must be positive")

    # Calculate middle band (SMA)
    middle_band = rolling_mean(ctx, period)

    # Calculate standard deviation
    std_deviation = rolling_std(ctx, period)

    # Use expressions to calculate upper and lower bands
    middle_expr = Expression(Literal(middle_band))
    std_expr = Expression(Literal(std_deviation))

    # Upper band = middle + (std * std_dev)
    upper_band = middle_expr + (std_expr * std_dev)
    
    # Lower band = middle - (std * std_dev)
    lower_band = middle_expr - (std_expr * std_dev)

    # Evaluate bands
    context = {}
    upper_series = upper_band.evaluate(context)
    lower_series = lower_band.evaluate(context)

    return upper_series, middle_band, lower_series
