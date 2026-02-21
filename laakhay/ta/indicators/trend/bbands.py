"""Bollinger Bands indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...primitives import rolling_mean, rolling_std  # type: ignore
from .. import Price, SeriesContext, register


@register(
    "bbands",
    aliases=["bb"],
    description="Bollinger Bands with upper, middle, and lower bands",
    output_metadata={
        "upper": {
            "role": "band_upper",
            "area_pair": "lower",
            "description": "Upper Bollinger Band",
        },
        "middle": {
            "role": "band_middle",
            "description": "Middle Bollinger Band (moving average)",
        },
        "lower": {
            "role": "band_lower",
            "area_pair": "upper",
            "description": "Lower Bollinger Band",
        },
    },
)
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

    # Calculate upper and lower bands using direct Series math since we already evaluated
    # the primitive rolling_mean and rolling_std components.
    upper_band = middle_band + (std_deviation * std_dev)
    lower_band = middle_band - (std_deviation * std_dev)

    return upper_band, middle_band, lower_band  # type: ignore


@register("bb_upper", description="Upper Bollinger Band")
def bb_upper(
    ctx: SeriesContext,
    period: int = 20,
    std_dev: float = 2.0,
) -> Series[Price]:
    """
    Convenience wrapper that returns only the upper Bollinger Band.
    """
    upper_band, _, _ = bbands(ctx, period=period, std_dev=std_dev)
    return upper_band


@register("bb_lower", description="Lower Bollinger Band")
def bb_lower(
    ctx: SeriesContext,
    period: int = 20,
    std_dev: float = 2.0,
) -> Series[Price]:
    """
    Convenience wrapper that returns only the lower Bollinger Band.
    """
    _, _, lower_band = bbands(ctx, period=period, std_dev=std_dev)
    return lower_band
