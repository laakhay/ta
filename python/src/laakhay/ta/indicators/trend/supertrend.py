"""Supertrend indicator using kernels."""

from __future__ import annotations

import ta_py

from ...core import Series
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

SUPERTREND_SPEC = IndicatorSpec(
    name="supertrend",
    description="Supertrend indicator",
    params={
        "period": ParamSpec(name="period", type=int, default=10, required=False),
        "multiplier": ParamSpec(name="multiplier", type=float, default=3.0, required=False),
    },
    outputs={
        "supertrend": OutputSpec(name="supertrend", type=Series, description="Supertrend line", role="line"),
        "direction": OutputSpec(
            name="direction", type=Series, description="Trend direction (1=bull, -1=bear)", role="line"
        ),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="supertrend"),
)


@register(spec=SUPERTREND_SPEC)
def supertrend(ctx: SeriesContext, period: int = 10, multiplier: float = 3.0) -> tuple[Series[Price], Series[Price]]:
    """
    Supertrend indicator.

    Returns (supertrend_line, direction_series).
    """
    if period <= 0:
        raise ValueError("Supertrend period must be positive")

    h, l, c = ctx.high, ctx.low, ctx.close
    if not (h and l and c) or len(c) == 0:
        empty = c.__class__(timestamps=(), values=(), symbol=c.symbol, timeframe=c.timeframe)
        return empty, empty

    st_vals, dir_vals = ta_py.supertrend(
        [float(v) for v in h.values],
        [float(v) for v in l.values],
        [float(v) for v in c.values],
        period,
        multiplier,
    )
    return (
        results_to_series(st_vals, c, value_class=Price),
        results_to_series(dir_vals, c, value_class=Price),
    )
