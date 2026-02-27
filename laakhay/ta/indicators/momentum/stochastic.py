"""Stochastic Oscillator indicator using primitives."""

from __future__ import annotations

import math

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

STOCHASTIC_SPEC = IndicatorSpec(
    name="stochastic",
    description="Stochastic Oscillator (%K and %D)",
    aliases=("stoch",),
    params={
        "k_period": ParamSpec(name="k_period", type=int, default=14, required=False),
        "d_period": ParamSpec(name="d_period", type=int, default=3, required=False),
        "smooth": ParamSpec(name="smooth", type=int, default=1, required=False),
    },
    outputs={
        "k": OutputSpec(name="k", type=Series, description="%K line of stochastic oscillator", role="osc_main"),
        "d": OutputSpec(name="d", type=Series, description="%D line (moving average of %K)", role="osc_signal"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("k_period", "d_period"),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="stochastic"),
)


@register(spec=STOCHASTIC_SPEC)
def stochastic(
    ctx: SeriesContext, k_period: int = 14, d_period: int = 3, smooth: int = 1
) -> tuple[Series[Price], Series[Price]]:
    """
    Stochastic Oscillator indicator using primitives.

    Returns (%K, %D) where:
    - %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
    - %D = Simple Moving Average of %K
    """
    if k_period <= 0 or d_period <= 0 or smooth <= 0:
        raise ValueError("Stochastic periods must be positive")

    # Validate required series
    required_series = ["high", "low", "close"]
    missing = [s for s in required_series if not hasattr(ctx, s)]
    if missing:
        raise ValueError(f"Stochastic requires series: {required_series}, missing: {missing}")

    close = ctx.close
    n = len(close)
    if n == 0:
        empty = CoreSeries[Price](timestamps=(), values=(), symbol=close.symbol, timeframe=close.timeframe)
        return empty, empty

    high = ctx.high
    low = ctx.low
    k_out, d_out = ta_py.stochastic_kd(
        [float(v) for v in high.values],
        [float(v) for v in low.values],
        [float(v) for v in close.values],
        k_period,
        d_period,
        smooth,
    )

    from .._utils import results_to_series

    k_series = results_to_series(k_out, close, value_class=Price)
    d_series = results_to_series(d_out, close, value_class=Price)

    return k_series, d_series


@register(
    spec=IndicatorSpec(
        name="stoch_k",
        description="Stochastic %K line",
        params={
            "k_period": ParamSpec(name="k_period", type=int, default=14, required=False),
            "d_period": ParamSpec(name="d_period", type=int, default=3, required=False),
        },
        outputs={"result": OutputSpec(name="result", type=Series, description="%K line", role="osc_main")},
        semantics=SemanticsSpec(
            required_fields=("high", "low", "close"),
            lookback_params=("k_period", "d_period"),
        ),
    )
)
def stoch_k(ctx: SeriesContext, k_period: int = 14, d_period: int = 3, smooth: int = 1) -> Series[Price]:
    k_series, _ = stochastic(ctx, k_period=k_period, d_period=d_period, smooth=smooth)
    return k_series


@register(
    spec=IndicatorSpec(
        name="stoch_d",
        description="Stochastic %D line",
        params={
            "k_period": ParamSpec(name="k_period", type=int, default=14, required=False),
            "d_period": ParamSpec(name="d_period", type=int, default=3, required=False),
        },
        outputs={"result": OutputSpec(name="result", type=Series, description="%D line", role="osc_signal")},
        semantics=SemanticsSpec(
            required_fields=("high", "low", "close"),
            lookback_params=("k_period", "d_period"),
        ),
    )
)
def stoch_d(ctx: SeriesContext, k_period: int = 14, d_period: int = 3, smooth: int = 1) -> Series[Price]:
    _, d_series = stochastic(ctx, k_period=k_period, d_period=d_period, smooth=smooth)
    return d_series
