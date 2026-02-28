"""Parabolic SAR (Stop and Reverse) indicator implementation."""

from __future__ import annotations

import ta_py
from decimal import Decimal

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...primitives.kernels.psar import PSARKernel
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

PSAR_SPEC = IndicatorSpec(
    name="psar",
    description="Parabolic SAR (Stop and Reverse)",
    params={
        "af_start": ParamSpec(name="af_start", type=float, default=0.02, required=False),
        "af_increment": ParamSpec(name="af_increment", type=float, default=0.02, required=False),
        "af_max": ParamSpec(name="af_max", type=float, default=0.2, required=False),
    },
    outputs={
        "sar": OutputSpec(name="sar", type=Series, description="SAR values", role="line"),
        "direction": OutputSpec(name="direction", type=Series, description="Direction (1=long, -1=short)", role="line"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("af_start", "af_increment", "af_max"),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="psar"),
)


@register(spec=PSAR_SPEC)
def psar(
    ctx: SeriesContext,
    af_start: float = 0.02,
    af_increment: float = 0.02,
    af_max: float = 0.2,
) -> tuple[Series[Price], Series[Price]]:
    """
    Parabolic SAR indicator.

    Returns (sar, direction).
    """
    if hasattr(ta_py, "psar"):
        sar_vals, dir_vals = ta_py.psar(
            [float(v) for v in ctx.high.values],
            [float(v) for v in ctx.low.values],
            [float(v) for v in ctx.close.values],
            af_start,
            af_increment,
            af_max,
        )
        return (
            results_to_series(sar_vals, ctx.close, value_class=Price),
            results_to_series(dir_vals, ctx.close, value_class=Price),
        )

    # Temporary fallback while ta_py upgrades.
    kernel = PSARKernel()
    n = len(ctx.close)

    if n == 0:
        empty = CoreSeries[Price](timestamps=(), values=(), symbol=ctx.close.symbol, timeframe=ctx.close.timeframe)
        return empty, empty

    # Standard approach for multi-output kernels in this library
    h = ctx.high
    l = ctx.low
    c = ctx.close

    xs = [(Decimal(str(h.values[i])), Decimal(str(l.values[i])), Decimal(str(c.values[i]))) for i in range(n)]

    out_sar = []
    out_dir = []

    # Initialize with first bar
    state = kernel.initialize(xs[:0], af_start=af_start, af_increment=af_increment, af_max=af_max)

    for i in range(n):
        state, (sar_val, dir_val) = kernel.step(state, xs[i])
        out_sar.append(sar_val)
        out_dir.append(dir_val)

    stamps = ctx.close.timestamps

    return (
        CoreSeries[Price](
            timestamps=stamps,
            values=tuple(Price(v) for v in out_sar),
            symbol=ctx.close.symbol,
            timeframe=ctx.close.timeframe,
            availability_mask=tuple(True for _ in out_sar),
        ),
        CoreSeries[Price](
            timestamps=stamps,
            values=tuple(Price(v) for v in out_dir),
            symbol=ctx.close.symbol,
            timeframe=ctx.close.timeframe,
            availability_mask=tuple(True for _ in out_dir),
        ),
    )
