"""MACD (Moving Average Convergence Divergence) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...primitives import rolling_ema
from .. import Expression, Literal, Price, SeriesContext, register


@register("macd", description="MACD (Moving Average Convergence Divergence)")
def macd(
    ctx: SeriesContext,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[Series[Price], Series[Price], Series[Price]]:
    """
    MACD indicator using primitives.

    Returns (macd_line, signal_line, histogram) where:
    - macd_line = EMA(fast) - EMA(slow)
    - signal_line = EMA(macd_line)
    - histogram = macd_line - signal_line
    """
    if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
        raise ValueError("MACD periods must be positive")
    if fast_period >= slow_period:
        raise ValueError("Fast period must be less than slow period")

    close = ctx.close
    if close is None or len(close) == 0:
        empty = close.__class__(timestamps=(), values=(), symbol=close.symbol, timeframe=close.timeframe)
        return empty, empty, empty

    # Calculate EMAs using rolling_ema primitive
    fast_ema = rolling_ema(ctx, fast_period)
    slow_ema = rolling_ema(ctx, slow_period)

    # Use expressions to calculate MACD line (fast_ema - slow_ema)
    fast_expr = Expression(Literal(fast_ema))
    slow_expr = Expression(Literal(slow_ema))
    macd_expr = fast_expr - slow_expr

    context = {}
    macd_line = macd_expr.evaluate(context)

    # Calculate signal line (EMA of MACD line)
    macd_ctx = SeriesContext(close=macd_line)
    signal_line = rolling_ema(macd_ctx, signal_period)

    # Use expressions to calculate histogram (macd_line - signal_line)
    histogram_expr = Expression(Literal(macd_line)) - Expression(Literal(signal_line))
    histogram = histogram_expr.evaluate(context)

    return macd_line, signal_line, histogram
