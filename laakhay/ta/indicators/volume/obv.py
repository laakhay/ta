"""On-Balance Volume (OBV) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...core.types import Qty, Price
from ...expressions.models import Literal
from ...expressions.operators import Expression
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...primitives import cumulative_sum, sign


@register("obv", description="On-Balance Volume indicator")
def obv(ctx: SeriesContext) -> Series[Qty]:
    """
    On-Balance Volume indicator using primitives.
    
    OBV = Cumulative sum of volume based on price direction:
    - If close > previous close: add volume
    - If close < previous close: subtract volume  
    - If close = previous close: add zero
    """
    # Validate required series
    if not hasattr(ctx, 'close') or not hasattr(ctx, 'volume'):
        raise ValueError("OBV requires both 'close' and 'volume' series in context")
    
    if len(ctx.close) != len(ctx.volume):
        raise ValueError("Close and volume series must have the same length")
    
    if len(ctx.close) == 0:
        return Series[Qty](timestamps=(), values=(), symbol=ctx.close.symbol, timeframe=ctx.close.timeframe)

    # Calculate price change signs and align volume
    price_signs = sign(ctx)
    aligned_volume = Series[Price](
        timestamps=ctx.volume.timestamps[1:],
        values=ctx.volume.values[1:],
        symbol=ctx.volume.symbol,
        timeframe=ctx.volume.timeframe,
    )
    
    # Calculate directed volume: volume * sign(price_change)
    directed_volume = (Expression(Literal(aligned_volume)) * Expression(Literal(price_signs))).evaluate({})

    # Calculate OBV as cumulative sum + first volume
    obv_series = cumulative_sum(SeriesContext(close=directed_volume))
    first_volume = Qty(str(ctx.volume.values[0]))
    
    return Series[Qty](
        timestamps=(ctx.volume.timestamps[0],) + obv_series.timestamps,
        values=(first_volume,) + tuple(Qty(str(val + first_volume)) for val in obv_series.values),
        symbol=obv_series.symbol,
        timeframe=obv_series.timeframe,
    )
