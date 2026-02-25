"""Donchian Channels indicator implementation."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
from ...core.types import Price
from ...primitives.rolling_ops import rolling_max, rolling_min
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)

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
)


@register(spec=DONCHIAN_SPEC)
def donchian(ctx: SeriesContext, period: int = 20) -> tuple[Series[Price], Series[Price], Series[Price]]:
    """
    Donchian Channels indicator.
    """
    if period <= 0:
        raise ValueError("Donchian period must be positive")

    upper = rolling_max(ctx, period, field="high")
    lower = rolling_min(ctx, period, field="low")
    middle = (upper + lower) / Decimal(2)

    return upper, lower, middle
