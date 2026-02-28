"""Donchian Channels indicator implementation."""

from __future__ import annotations

import ta_py

from ...core import Series
from ...core.types import Price
from ...primitives.rolling_ops import rolling_max, rolling_min
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

DONCHIAN_SPEC = IndicatorSpec(
    name="donchian",
    description="Donchian Channels",
    params={"period": ParamSpec(name="period", type=int, default=20, required=False)},
    outputs={
        "upper": OutputSpec(name="upper", type=Series, description="Upper channel (rolling max high)", role="line"),
        "lower": OutputSpec(name="lower", type=Series, description="Lower channel (rolling min low)", role="line"),
        "middle": OutputSpec(name="middle", type=Series, description="Middle channel ((upper+lower)/2)", role="line"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low"),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="donchian"),
)


@register(spec=DONCHIAN_SPEC)
def donchian(ctx: SeriesContext, period: int = 20) -> tuple[Series[Price], Series[Price], Series[Price]]:
    """
    Donchian Channels indicator.
    """
    if period <= 0:
        raise ValueError("Donchian period must be positive")

    if hasattr(ta_py, "donchian"):
        upper_vals, lower_vals, middle_vals = ta_py.donchian(
            [float(v) for v in ctx.high.values],
            [float(v) for v in ctx.low.values],
            period,
        )
        return (
            results_to_series(upper_vals, ctx.close, value_class=Price),
            results_to_series(lower_vals, ctx.close, value_class=Price),
            results_to_series(middle_vals, ctx.close, value_class=Price),
        )

    # Temporary fallback while ta_py upgrades.
    upper = rolling_max(ctx, period, field="high")
    lower = rolling_min(ctx, period, field="low")
    middle = (upper + lower) / 2

    return upper, lower, middle
