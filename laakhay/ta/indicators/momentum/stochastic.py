"""Stochastic Oscillator indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...core.types import Price
from ...expr.algebra.models import Literal
from ...expr.algebra.operators import Expression
from ...primitives import rolling_max, rolling_mean, rolling_min
from ...registry.models import SeriesContext
from ...registry.registry import register


@register("stochastic", description="Stochastic Oscillator (%K and %D)")
def stochastic(ctx: SeriesContext, k_period: int = 14, d_period: int = 3) -> tuple[Series[Price], Series[Price]]:
    """
    Stochastic Oscillator indicator using primitives.

    Returns (%K, %D) where:
    - %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
    - %D = Simple Moving Average of %K
    """
    if k_period <= 0 or d_period <= 0:
        raise ValueError("Stochastic periods must be positive")

    # Validate required series
    required_series = ["high", "low", "close"]
    missing = [s for s in required_series if not hasattr(ctx, s)]
    if missing:
        raise ValueError(f"Stochastic requires series: {required_series}, missing: {missing}")

    # Validate series lengths
    series_lengths = [len(getattr(ctx, s)) for s in required_series]
    if len(set(series_lengths)) > 1:
        raise ValueError("All series must have the same length")

    # Calculate rolling max and min
    highest_high = rolling_max(SeriesContext(close=ctx.high), k_period)
    lowest_low = rolling_min(SeriesContext(close=ctx.low), k_period)

    # Handle insufficient data
    if len(highest_high) == 0 or len(lowest_low) == 0:
        empty_series = Series[Price](
            timestamps=(),
            values=(),
            symbol=ctx.close.symbol,
            timeframe=ctx.close.timeframe,
        )
        return empty_series, empty_series

    # Align close series with rolling results (take last N values)
    aligned_close = Series[Price](
        timestamps=ctx.close.timestamps[-(len(highest_high)) :],
        values=ctx.close.values[-(len(highest_high)) :],
        symbol=ctx.close.symbol,
        timeframe=ctx.close.timeframe,
    )

    # Calculate %K using expressions
    close_expr = Expression(Literal(aligned_close))
    high_expr = Expression(Literal(highest_high))
    low_expr = Expression(Literal(lowest_low))

    # Handle identical high/low case
    if all(h == l for h, l in zip(highest_high.values, lowest_low.values, strict=False)):
        k_series = Series[Price](
            timestamps=aligned_close.timestamps,
            values=tuple(Price("50.0") for _ in aligned_close.values),
            symbol=aligned_close.symbol,
            timeframe=aligned_close.timeframe,
        )
    else:
        # %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
        k_expr = ((close_expr - low_expr) / (high_expr - low_expr + 1e-10)) * 100
        k_series = k_expr.evaluate({})

    # Calculate %D using rolling_mean on %K
    d_series = rolling_mean(SeriesContext(close=k_series), d_period)

    return k_series, d_series
