"""Vortex Indicator (VI) implementation."""

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

VORTEX_SPEC = IndicatorSpec(
    name="vortex",
    description="Vortex Indicator (VI)",
    params={"period": ParamSpec(name="period", type=int, default=14, required=False)},
    outputs={
        "plus": OutputSpec(name="plus", type=Series, description="VI+", role="line"),
        "minus": OutputSpec(name="minus", type=Series, description="VI-", role="line"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="vortex"),
)


@register(spec=VORTEX_SPEC)
def vortex(ctx: SeriesContext, period: int = 14) -> tuple[Series[Price], Series[Price]]:
    """
    Vortex Indicator (VI).

    VI+ = Sum(abs(High - Prev Low), period) / Sum(True Range, period)
    VI- = Sum(abs(Low - Prev High), period) / Sum(True Range, period)
    """
    if period <= 0:
        raise ValueError("Vortex period must be positive")

    h, l, c = ctx.high, ctx.low, ctx.close
    n = len(c)
    if n == 0:
        empty = CoreSeries[Price](timestamps=(), values=(), symbol=c.symbol, timeframe=c.timeframe)
        return empty, empty

    plus_vals, minus_vals = ta_py.vortex(
        [float(v) for v in h.values],
        [float(v) for v in l.values],
        [float(v) for v in c.values],
        period,
    )
    return (
        results_to_series(plus_vals, c, value_class=Price),
        results_to_series(minus_vals, c, value_class=Price),
    )
