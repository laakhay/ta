"""Hull Moving Average (HMA) indicator implementation."""

from __future__ import annotations

import math

from ...core import Series
from ...core.types import Price
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)
from .wma import wma

HMA_SPEC = IndicatorSpec(
    name="hma",
    description="Hull Moving Average (fast, lag-reduced)",
    params={"period": ParamSpec(name="period", type=int, default=14, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="HMA values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("close",),
        lookback_params=("period",),
    ),
)


@register(spec=HMA_SPEC)
def hma(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Hull Moving Average (HMA) implementation.

    Formula:
    WMA1 = WMA(n/2, close)
    WMA2 = WMA(n, close)
    Raw_HMA = 2 * WMA1 - WMA2
    HMA = WMA(sqrt(n), Raw_HMA)
    """
    if period <= 0:
        raise ValueError("HMA period must be positive")

    # 1. Calculate WMA(period/2)
    wma_half = wma(ctx, period=period // 2)

    # 2. Calculate WMA(period)
    wma_full = wma(ctx, period=period)

    # 3. Raw HMA series: 2 * WMA(n/2) - WMA(n)
    raw_hma_series = (wma_half * 2) - wma_full

    # 4. Final HMA: WMA(sqrt(n), Raw_HMA)
    sqrt_period = int(math.sqrt(period))
    if sqrt_period < 1:
        sqrt_period = 1

    # We need a new context for the final WMA call
    new_ctx = SeriesContext(close=raw_hma_series)
    return wma(new_ctx, period=sqrt_period)
