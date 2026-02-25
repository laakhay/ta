"""Stochastic Oscillator indicator using primitives."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...primitives.rolling_ops import rolling_max, rolling_mean, rolling_min
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
def stochastic(ctx: SeriesContext, k_period: int = 14, d_period: int = 3) -> tuple[Series[Price], Series[Price]]:
    """
    Stochastic Oscillator indicator using primitives.

    Returns (%K, %D) where:
    - %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
    - %D = Simple Moving Average of %K
    """
    if k_period <= 0 or d_period <= 0:
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

    # Calculate rolling max and min (full length)
    highest_high = rolling_max(SeriesContext(close=ctx.high), k_period)
    lowest_low = rolling_min(SeriesContext(close=ctx.low), k_period)

    # %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
    k_values = []
    k_mask = []

    for i in range(n):
        if not highest_high.availability_mask[i]:
            k_values.append(Decimal(0))
            k_mask.append(False)
            continue

        c_val = Decimal(str(close.values[i]))
        h_val = Decimal(str(highest_high.values[i]))
        l_val = Decimal(str(lowest_low.values[i]))

        denom = h_val - l_val
        if denom == 0:
            k_values.append(Decimal("50"))
        else:
            k_values.append(Decimal("100") * (c_val - l_val) / denom)
        k_mask.append(True)

    k_series = CoreSeries[Price](
        timestamps=close.timestamps,
        values=tuple(Price(v) for v in k_values),
        symbol=close.symbol,
        timeframe=close.timeframe,
        availability_mask=tuple(k_mask),
    )

    # Calculate %D using rolling_mean on %K
    d_series = rolling_mean(SeriesContext(close=k_series), d_period)

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
def stoch_k(ctx: SeriesContext, k_period: int = 14, d_period: int = 3) -> Series[Price]:
    k_series, _ = stochastic(ctx, k_period=k_period, d_period=d_period)
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
def stoch_d(ctx: SeriesContext, k_period: int = 14, d_period: int = 3) -> Series[Price]:
    _, d_series = stochastic(ctx, k_period=k_period, d_period=d_period)
    return d_series
