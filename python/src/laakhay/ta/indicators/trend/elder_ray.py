"""Elder Ray Index (Bull and Bear Power)."""

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

ELDER_RAY_SPEC = IndicatorSpec(
    name="elder_ray",
    description="Elder Ray Index (Bull and Bear Power)",
    params={"period": ParamSpec(name="period", type=int, default=13, required=False)},
    outputs={
        "bull": OutputSpec(name="bull", type=Series, description="Bull Power", role="histogram"),
        "bear": OutputSpec(name="bear", type=Series, description="Bear Power", role="histogram"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="elder_ray"),
)


@register(spec=ELDER_RAY_SPEC)
def elder_ray(ctx: SeriesContext, period: int = 13) -> tuple[Series[Price], Series[Price]]:
    """
    Elder Ray Index.

    EMA = EMA(close, period)
    Bull Power = High - EMA
    Bear Power = Low - EMA
    """
    if period <= 0:
        raise ValueError("Elder Ray period must be positive")

    bull_vals, bear_vals = ta_py.elder_ray(
        [float(v) for v in ctx.high.values],
        [float(v) for v in ctx.low.values],
        [float(v) for v in ctx.close.values],
        period,
    )
    return (
        results_to_series(bull_vals, ctx.close, value_class=Price),
        results_to_series(bear_vals, ctx.close, value_class=Price),
    )
