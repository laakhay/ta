"""On-Balance Volume (OBV) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...core.types import Price, Qty
from ...primitives.elementwise_ops import cumulative_sum, sign
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)

OBV_SPEC = IndicatorSpec(
    name="obv",
    description="On-Balance Volume indicator",
    outputs={"result": OutputSpec(name="result", type=Series, description="OBV values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("close", "volume"),
        default_lookback=2,
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="obv"),
)


@register(spec=OBV_SPEC)
def obv(ctx: SeriesContext) -> Series[Qty]:
    """
    On-Balance Volume indicator using primitives.

    OBV = Cumulative sum of volume based on price direction:
    - If close > previous close: add volume
    - If close < previous close: subtract volume
    - If close = previous close: add zero
    """
    close = getattr(ctx, "close", None)
    volume = getattr(ctx, "volume", None)
    if close is None or volume is None:
        raise ValueError("OBV requires both 'close' and 'volume' series")
    if len(close) != len(volume):
        raise ValueError("Close and volume series must have the same length")
    if len(close) == 0:
        return close.__class__(timestamps=(), values=(), symbol=close.symbol, timeframe=close.timeframe)
    if len(close) == 1:
        # For a single value, output series should also be length 1 and return input's meta
        return close.__class__(
            timestamps=close.timestamps,
            values=(volume.values[0],),
            symbol=close.symbol,
            timeframe=close.timeframe,
        )

    # Calculate price change signs and align volume
    price_signs = sign(ctx)
    aligned_volume = Series[Price](
        timestamps=ctx.volume.timestamps[1:],
        values=ctx.volume.values[1:],
        symbol=ctx.volume.symbol,
        timeframe=ctx.volume.timeframe,
    )

    # Calculate directed volume: volume * sign(price_change)
    directed_volume = aligned_volume * price_signs

    # Calculate OBV as cumulative sum + first volume
    obv_series = cumulative_sum(SeriesContext(close=directed_volume))
    first_volume = Qty(str(ctx.volume.values[0]))

    return Series[Qty](
        timestamps=(ctx.volume.timestamps[0],) + obv_series.timestamps,
        values=(first_volume,) + tuple(Qty(str(val + first_volume)) for val in obv_series.values),
        symbol=obv_series.symbol,
        timeframe=obv_series.timeframe,
    )
