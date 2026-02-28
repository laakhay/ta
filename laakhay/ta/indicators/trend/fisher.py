"""Fisher Transform indicator implementation."""

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


FISHER_SPEC = IndicatorSpec(
    name="fisher",
    description="Fisher Transform",
    params={"period": ParamSpec(name="period", type=int, default=9, required=False)},
    outputs={
        "fisher": OutputSpec(name="fisher", type=Series, description="Fisher Transform", role="line"),
        "signal": OutputSpec(name="signal", type=Series, description="Signal Line (Fisher delayed by 1)", role="line"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low"),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="fisher"),
)


@register(spec=FISHER_SPEC)
def fisher(ctx: SeriesContext, period: int = 9) -> tuple[Series[Price], Series[Price]]:
    """
    Fisher Transform indicator.
    """
    if period <= 0:
        raise ValueError("Fisher period must be positive")

    fisher_vals, signal_vals = ta_py.fisher(
        [float(v) for v in ctx.high.values],
        [float(v) for v in ctx.low.values],
        period,
    )
    return (
        results_to_series(fisher_vals, ctx.high, value_class=Price),
        results_to_series(signal_vals, ctx.high, value_class=Price),
    )
