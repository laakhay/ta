"""MACD (Moving Average Convergence Divergence) indicator."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Tuple

from ...core import Series
from ...core.types import Price
from ...registry.registry import register
from ...registry.models import SeriesContext
from ...expressions.operators import Expression
from ...expressions.models import Literal, BinaryOp, OperatorType
from ..utils import _select_source_series
from .ema import ema


@register("macd", description="MACD (Moving Average Convergence Divergence)")
def macd(
    ctx: SeriesContext, 
    fast_period: int = 12, 
    slow_period: int = 26, 
    signal_period: int = 9
) -> Tuple[Series[Price], Series[Price], Series[Price]]:
    """
    MACD indicator.
    
    Returns (macd_line, signal_line, histogram) where:
    - macd_line = EMA(fast) - EMA(slow)
    - signal_line = EMA(macd_line)
    - histogram = macd_line - signal_line
    """
    if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
        raise ValueError("MACD periods must be positive")
    if fast_period >= slow_period:
        raise ValueError("Fast period must be less than slow period")
    
    source = _select_source_series(ctx)
    n = len(source)
    if n == 0:
        empty = Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)
        return empty, empty, empty
    
    # Calculate EMAs using registered ema function
    fast_ema = ema(ctx, fast_period)
    slow_ema = ema(ctx, slow_period)
    
    # Use expressions to calculate MACD line (fast_ema - slow_ema)
    fast_expr = Expression(Literal(fast_ema))
    slow_expr = Expression(Literal(slow_ema))
    macd_expr = fast_expr - slow_expr
    
    context = {}
    macd_line = macd_expr.evaluate(context)
    
    # Calculate signal line (EMA of MACD line)
    # Create a new context with macd_line as the source
    from ...registry.models import SeriesContext
    macd_ctx = SeriesContext(close=macd_line)
    signal_line = ema(macd_ctx, signal_period)
    
    # Use expressions to calculate histogram (macd_line - signal_line)
    macd_expr2 = Expression(Literal(macd_line))
    signal_expr = Expression(Literal(signal_line))
    histogram_expr = macd_expr2 - signal_expr
    
    histogram = histogram_expr.evaluate(context)
    
    return macd_line, signal_line, histogram
