"""Awesome Oscillator (AO) indicator implementation."""

from __future__ import annotations

from ...core import Series
from ...core.types import Price
from ...primitives.select import _select_field
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)
from ..trend.sma import sma

AO_SPEC = IndicatorSpec(
    name="ao",
    description="Awesome Oscillator",
    params={
        "fast_period": ParamSpec(name="fast_period", type=int, default=5, required=False),
        "slow_period": ParamSpec(name="slow_period", type=int, default=34, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="AO values", role="column")},
    semantics=SemanticsSpec(
        required_fields=("high", "low"),
        lookback_params=("fast_period", "slow_period"),
    ),
)


@register(spec=AO_SPEC)
def ao(ctx: SeriesContext, fast_period: int = 5, slow_period: int = 34) -> Series[Price]:
    """
    Awesome Oscillator (AO).

    AO = SMA(Median Price, 5) - SMA(Median Price, 34)
    """
    if fast_period <= 0 or slow_period <= 0:
        raise ValueError("Periods must be positive")

    mp = _select_field(ctx, "median_price")
    new_ctx = SeriesContext(price=mp)

    fast_sma = sma(new_ctx, period=fast_period)
    slow_sma = sma(new_ctx, period=slow_period)

    return fast_sma - slow_sma
