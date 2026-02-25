"""Elder Ray Index (Bull and Bear Power)."""

from __future__ import annotations

from ...core import Series
from ...core.types import Price
from ...primitives.rolling_ops import rolling_ema
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)

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

    ema = rolling_ema(ctx, period=period)

    bull_power = ctx.high - ema
    bear_power = ctx.low - ema

    return bull_power, bear_power
