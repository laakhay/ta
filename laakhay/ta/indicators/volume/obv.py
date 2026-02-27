"""On-Balance Volume (OBV) indicator using primitives."""

from __future__ import annotations

import math

import ta_py

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Qty
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
    out = ta_py.obv([float(v) for v in close.values], [float(v) for v in volume.values])
    return CoreSeries[Qty](
        timestamps=close.timestamps,
        values=tuple(Qty("NaN") if math.isnan(v) else Qty(str(v)) for v in out),
        symbol=close.symbol,
        timeframe=close.timeframe,
        availability_mask=tuple(not math.isnan(v) for v in out),
    )
