"""Parabolic SAR (Stop and Reverse) indicator implementation."""

from __future__ import annotations

import ta_py

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
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
    n = len(ctx.close)
    if n == 0:
        empty = CoreSeries[Price](timestamps=(), values=(), symbol=ctx.close.symbol, timeframe=ctx.close.timeframe)
        return empty, empty

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
