"""Money Flow Index (MFI) indicator implementation."""

from __future__ import annotations

import ta_py
from decimal import Decimal

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...primitives.kernels.mfi import MFIKernel
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)
from .._utils import results_to_series

MFI_SPEC = IndicatorSpec(
    name="mfi",
    description="Money Flow Index",
    params={"period": ParamSpec(name="period", type=int, default=14, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="MFI values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close", "volume"),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="mfi"),
)


@register(spec=MFI_SPEC)
def mfi(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Money Flow Index (MFI) indicator.
    """
    if period <= 0:
        raise ValueError("MFI period must be positive")

    if hasattr(ta_py, "mfi"):
        out_vals = ta_py.mfi(
            [float(v) for v in ctx.high.values],
            [float(v) for v in ctx.low.values],
            [float(v) for v in ctx.close.values],
            [float(v) for v in ctx.volume.values],
            period,
        )
        return results_to_series(out_vals, ctx.close, value_class=Price)

    # Temporary fallback while ta_py upgrades.
    kernel = MFIKernel()
    n = len(ctx.close)

    if n == 0:
        return CoreSeries[Price](timestamps=(), values=(), symbol=ctx.close.symbol, timeframe=ctx.close.timeframe)

    h = ctx.high
    l = ctx.low
    c = ctx.close
    v = ctx.volume

    xs = [
        (Decimal(str(h.values[i])), Decimal(str(l.values[i])), Decimal(str(c.values[i])), Decimal(str(v.values[i])))
        for i in range(n)
    ]

    out_values = []

    # Initialize
    state = kernel.initialize(xs[:0], period=period)

    for i in range(n):
        state, val = kernel.step(state, xs[i])
        out_values.append(val)

    # Use mask to match library pattern: values are 0 before period is reached
    mask = [i >= period for i in range(n)]

    return CoreSeries[Price](
        timestamps=ctx.close.timestamps,
        values=tuple(Price(v) for v in out_values),
        symbol=ctx.close.symbol,
        timeframe=ctx.close.timeframe,
        availability_mask=tuple(mask),
    )
