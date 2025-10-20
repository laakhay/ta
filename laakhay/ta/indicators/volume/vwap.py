"""Volume Weighted Average Price (VWAP) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...core.types import Price
from ...expressions.models import Literal
from ...expressions.operators import Expression
from ...registry.models import SeriesContext
from ...registry.registry import register
from ..primitives import typical_price, cumulative_sum


@register("vwap", description="Volume Weighted Average Price")
def vwap(ctx: SeriesContext) -> Series[Price]:
    """
    Volume Weighted Average Price indicator using primitives.
    
    VWAP = Sum(Price * Volume) / Sum(Volume)
    where Price = (High + Low + Close) / 3
    """
    # Get required series
    required_series = ['high', 'low', 'close', 'volume']
    missing = [s for s in required_series if not hasattr(ctx, s)]
    if missing:
        raise ValueError(f"VWAP requires series: {required_series}, missing: {missing}")
    
    # Validate series lengths
    series_lengths = [len(getattr(ctx, s)) for s in required_series]
    if len(set(series_lengths)) > 1:
        raise ValueError("All series must have the same length")

    # Calculate typical price using primitive
    typical = typical_price(ctx)
    
    # Calculate Price * Volume using expressions
    typical_expr = Expression(Literal(typical))
    volume_expr = Expression(Literal(ctx.volume))
    pv_expr = typical_expr * volume_expr

    # Evaluate Price * Volume
    context = {}
    pv_series = pv_expr.evaluate(context)

    # Calculate cumulative sums
    pv_ctx = SeriesContext(close=pv_series)
    vol_ctx = SeriesContext(close=ctx.volume)
    
    cumulative_pv = cumulative_sum(pv_ctx)
    cumulative_vol = cumulative_sum(vol_ctx)

    # VWAP = cumulative_pv / cumulative_vol using expressions
    # Handle zero volume case by falling back to typical price
    pv_cum_expr = Expression(Literal(cumulative_pv))
    vol_cum_expr = Expression(Literal(cumulative_vol))
    
    # Check if all volumes are zero
    all_zero_volume = all(vol == 0 for vol in ctx.volume.values)
    
    if all_zero_volume:
        # Fallback to typical price when volume is zero
        return typical_price(ctx)
    else:
        # Direct division without epsilon - let the expression system handle it
        vwap_expr = pv_cum_expr / vol_cum_expr
        return vwap_expr.evaluate(context)
