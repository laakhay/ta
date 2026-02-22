"""Volume Weighted Average Price (VWAP) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...core.types import Price
from ...primitives.elementwise_ops import cumulative_sum, typical_price
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)

VWAP_SPEC = IndicatorSpec(
    name="vwap",
    description="Volume Weighted Average Price",
    outputs={"result": OutputSpec(name="result", type=Series, description="VWAP values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close", "volume"),
        default_lookback=1,
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="vwap"),
)


@register(spec=VWAP_SPEC)
def vwap(ctx: SeriesContext) -> Series[Price]:
    """
    Volume Weighted Average Price indicator using primitives.

    VWAP = Sum(Price * Volume) / Sum(Volume)
    where Price = (High + Low + Close) / 3
    """
    # Validate required series
    required_series = ["high", "low", "close", "volume"]
    missing = [s for s in required_series if not hasattr(ctx, s)]
    if missing:
        raise ValueError(f"VWAP requires series: {required_series}, missing: {missing}")

    series_lengths = [len(getattr(ctx, s)) for s in required_series]
    if len(set(series_lengths)) > 1:
        raise ValueError("All series must have the same length")

    # Handle zero volume case
    if all(vol == 0 for vol in ctx.volume.values):
        return typical_price(ctx)

    # Calculate VWAP: cumulative(typical*volume) / cumulative(volume)
    typical = typical_price(ctx)
    pv_series = typical * ctx.volume

    cumulative_pv = cumulative_sum(SeriesContext(close=pv_series))
    cumulative_vol = cumulative_sum(SeriesContext(close=ctx.volume))

    return cumulative_pv / cumulative_vol
