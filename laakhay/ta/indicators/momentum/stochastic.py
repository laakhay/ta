"""Stochastic Oscillator indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...core.types import Price
from ...expressions.models import Literal
from ...expressions.operators import Expression
from ...registry.models import SeriesContext
from ...registry.registry import register
from ..primitives import rolling_max, rolling_mean, rolling_min


@register("stochastic", description="Stochastic Oscillator (%K and %D)")
def stochastic(
    ctx: SeriesContext,
    k_period: int = 14,
    d_period: int = 3
) -> tuple[Series[Price], Series[Price]]:
    """
    Stochastic Oscillator indicator using primitives.
    
    Returns (%K, %D) where:
    - %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
    - %D = Simple Moving Average of %K
    """
    if k_period <= 0 or d_period <= 0:
        raise ValueError("Stochastic periods must be positive")

    # Get required series
    required_series = ['high', 'low', 'close']
    missing = [s for s in required_series if not hasattr(ctx, s)]
    if missing:
        raise ValueError(f"Stochastic requires series: {required_series}, missing: {missing}")
    
    # Validate series lengths
    series_lengths = [len(getattr(ctx, s)) for s in required_series]
    if len(set(series_lengths)) > 1:
        raise ValueError("All series must have the same length")

    # Calculate rolling max and min on individual series
    high_ctx = SeriesContext(close=ctx.high)
    low_ctx = SeriesContext(close=ctx.low)

    highest_high = rolling_max(high_ctx, k_period)
    lowest_low = rolling_min(low_ctx, k_period)

    # Calculate %K using expressions
    # %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
    
    # Handle insufficient data case
    if len(highest_high) == 0 or len(lowest_low) == 0:
        return Series[Price](
            timestamps=(),
            values=(),
            symbol=ctx.close.symbol,
            timeframe=ctx.close.timeframe,
        ), Series[Price](
            timestamps=(),
            values=(),
            symbol=ctx.close.symbol,
            timeframe=ctx.close.timeframe,
        )
    
    # Align close series with rolling results
    # Find the common timestamps between close and rolling results
    close_timestamps = ctx.close.timestamps
    high_timestamps = highest_high.timestamps
    low_timestamps = lowest_low.timestamps
    
    # Find common timestamps
    common_timestamps = []
    aligned_close_values = []
    
    for i, timestamp in enumerate(close_timestamps):
        if timestamp in high_timestamps and timestamp in low_timestamps:
            common_timestamps.append(timestamp)
            aligned_close_values.append(ctx.close.values[i])
    
    if len(common_timestamps) == 0:
        return Series[Price](
            timestamps=(),
            values=(),
            symbol=ctx.close.symbol,
            timeframe=ctx.close.timeframe,
        ), Series[Price](
            timestamps=(),
            values=(),
            symbol=ctx.close.symbol,
            timeframe=ctx.close.timeframe,
        )
    
    # Create aligned close series
    aligned_close = Series[Price](
        timestamps=tuple(common_timestamps),
        values=tuple(aligned_close_values),
        symbol=ctx.close.symbol,
        timeframe=ctx.close.timeframe,
    )
    
    close_expr = Expression(Literal(aligned_close))
    high_expr = Expression(Literal(highest_high))
    low_expr = Expression(Literal(lowest_low))

    # Calculate %K
    numerator = close_expr - low_expr
    denominator = high_expr - low_expr
    
    # Handle case where high == low (should return 50.0)
    # Check if all high values equal low values
    all_identical = all(h == l for h, l in zip(highest_high.values, lowest_low.values))
    
    if all_identical:
        # When high == low, return 50.0 for all values
        k_series = Series[Price](
            timestamps=aligned_close.timestamps,
            values=tuple(Price('50.0') for _ in aligned_close.values),
            symbol=aligned_close.symbol,
            timeframe=aligned_close.timeframe,
        )
    else:
        # Add small epsilon to avoid division by zero
        epsilon = 1e-10
        k_expr = (numerator / (denominator + epsilon)) * 100
        context = {}
        k_series = k_expr.evaluate(context)

    # Calculate %D using rolling_mean on %K
    k_ctx = SeriesContext(close=k_series)
    d_series = rolling_mean(k_ctx, d_period)
    
    return k_series, d_series
