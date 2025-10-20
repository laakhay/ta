"""Bollinger Bands indicator."""

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
from .sma import sma


@register("bbands", description="Bollinger Bands with upper, middle, and lower bands")
def bbands(
    ctx: SeriesContext, 
    period: int = 20, 
    std_dev: float = 2.0
) -> Tuple[Series[Price], Series[Price], Series[Price]]:
    """
    Bollinger Bands (BBands) indicator.
    
    Returns (upper_band, middle_band, lower_band) where:
    - middle_band = SMA(period)
    - upper_band = middle_band + (std_dev * standard_deviation)
    - lower_band = middle_band - (std_dev * standard_deviation)
    """
    if period <= 0:
        raise ValueError("Bollinger Bands period must be positive")
    if std_dev <= 0:
        raise ValueError("Standard deviation multiplier must be positive")
    
    source = _select_source_series(ctx)
    n = len(source)
    if n == 0:
        empty = Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)
        return empty, empty, empty
    
    # Calculate middle band (SMA) using registered sma function
    middle_band = sma(ctx, period)
    
    if len(middle_band) == 0:
        empty = Series[Price](timestamps=(), values=(), symbol=source.symbol, timeframe=source.timeframe)
        return empty, empty, empty
    
    # Calculate standard deviation manually (no utility function needed)
    std_values: list[Price] = []
    std_stamps: list[Any] = []
    
    for i in range(len(middle_band)):
        # Get the corresponding window in the original series
        start_idx = i
        end_idx = start_idx + period
        
        # Calculate standard deviation for this window
        window_values = [Decimal(str(source.values[j])) for j in range(start_idx, end_idx)]
        mean = Decimal(str(middle_band.values[i]))
        
        variance = Decimal('0')
        for val in window_values:
            diff = val - mean
            variance += diff * diff
        variance = variance / Decimal(str(period))
        std_deviation = variance.sqrt()
        
        std_values.append(Price(std_deviation))
        std_stamps.append(middle_band.timestamps[i])
    
    std_series = Series[Price](
        timestamps=tuple(std_stamps),
        values=tuple(std_values),
        symbol=source.symbol,
        timeframe=source.timeframe,
    )
    
    # Use expressions to calculate bands
    middle_expr = Expression(Literal(middle_band))
    std_expr = Expression(Literal(std_series))
    
    # upper_band = middle_band + (std_dev * std_deviation)
    upper_expr = middle_expr + (std_expr * std_dev)
    
    # lower_band = middle_band - (std_dev * std_deviation)  
    lower_expr = middle_expr - (std_expr * std_dev)
    
    context = {}
    upper_band = upper_expr.evaluate(context)
    lower_band = lower_expr.evaluate(context)
    
    return upper_band, middle_band, lower_band
