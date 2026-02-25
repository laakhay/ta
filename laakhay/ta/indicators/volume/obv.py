"""On-Balance Volume (OBV) indicator using primitives."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ...core import Series
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
    if len(close) == 1:
        # For a single value, output series should also be length 1 and return input's meta
        return close.__class__(
            timestamps=close.timestamps,
            values=(volume.values[0],),
            symbol=close.symbol,
            timeframe=close.timeframe,
        )

    from ...primitives.kernel import run_kernel
    from ...primitives.kernels.obv import OBVKernel

    # Zip close and volume for kernel
    close_vals = [Decimal(str(v)) for v in close.values]
    vol_vals = [Decimal(str(v)) for v in volume.values]
    cv_series = Series[Any](
        timestamps=close.timestamps,
        values=tuple(zip(close_vals, vol_vals, strict=True)),
        symbol=close.symbol,
        timeframe=close.timeframe,
    )

    res = run_kernel(cv_series, OBVKernel(), min_periods=1, coerce_input=lambda x: x)

    return Series[Qty](
        timestamps=res.timestamps,
        values=tuple(Qty(str(v)) for v in res.values),
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )
