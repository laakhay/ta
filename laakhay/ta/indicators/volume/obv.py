"""On-Balance Volume (OBV) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...core.types import Qty, Price
from ...expressions.models import Literal
from ...expressions.operators import Expression
from ...registry.models import SeriesContext
from ...registry.registry import register
from ..primitives import cumulative_sum, sign


@register("obv", description="On-Balance Volume indicator")
def obv(ctx: SeriesContext) -> Series[Qty]:
    """
    On-Balance Volume indicator using primitives.
    
    OBV = Cumulative sum of volume based on price direction:
    - If close > previous close: add volume
    - If close < previous close: subtract volume  
    - If close = previous close: add zero
    """
    # Get required series
    if not hasattr(ctx, 'close') or not hasattr(ctx, 'volume'):
        raise ValueError("OBV requires both 'close' and 'volume' series in context")
    
    # Validate series lengths
    if len(ctx.close) != len(ctx.volume):
        raise ValueError("Close and volume series must have the same length")
    
    # Handle empty series
    if len(ctx.close) == 0:
        return Series[Qty](
            timestamps=(),
            values=(),
            symbol=ctx.close.symbol,
            timeframe=ctx.close.timeframe,
        )

    # Calculate price change signs using sign primitive
    price_signs = sign(ctx)
    
    # Align volume series with price signs (skip first volume value)
    # since sign returns one less value than input
    aligned_volume = Series[Price](
        timestamps=ctx.volume.timestamps[1:],  # Skip first timestamp
        values=ctx.volume.values[1:],          # Skip first value
        symbol=ctx.volume.symbol,
        timeframe=ctx.volume.timeframe,
    )
    
    # Create volume direction based on price changes
    # Volume direction = volume * sign(price_change)
    volume_expr = Expression(Literal(aligned_volume))
    sign_expr = Expression(Literal(price_signs))
    directed_volume_expr = volume_expr * sign_expr

    # Evaluate directed volume
    context = {}
    directed_volume = directed_volume_expr.evaluate(context)

    # Calculate OBV as cumulative sum of directed volume
    obv_ctx = SeriesContext(close=directed_volume)
    obv_series = cumulative_sum(obv_ctx)
    
    # Prepend the first volume value to match expected OBV behavior
    first_volume = ctx.volume.values[0]
    first_timestamp = ctx.volume.timestamps[0]
    
    # Create final OBV series with first volume prepended
    final_timestamps = (first_timestamp,) + obv_series.timestamps
    final_values = (Qty(str(first_volume)),) + tuple(Qty(str(val + first_volume)) for val in obv_series.values)
    
    return Series[Qty](
        timestamps=final_timestamps,
        values=final_values,
        symbol=obv_series.symbol,
        timeframe=obv_series.timeframe,
    )
