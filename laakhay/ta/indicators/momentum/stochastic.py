"""Stochastic Oscillator indicator using primitives."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
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

    # Validate series lengths
    series_lengths = [len(getattr(ctx, s)) for s in required_series]
    if len(set(series_lengths)) > 1:
        raise ValueError("All series must have the same length")

    # Calculate rolling max and min
    highest_high = rolling_max(SeriesContext(close=ctx.high), k_period)
    lowest_low = rolling_min(SeriesContext(close=ctx.low), k_period)

    # Handle insufficient data
    if len(highest_high) == 0 or len(lowest_low) == 0:
        empty_series = Series[Price](
            timestamps=(),
            values=(),
            symbol=ctx.close.symbol,
            timeframe=ctx.close.timeframe,
        )
        return empty_series, empty_series

    # Align close series with rolling results (take last N values)
    aligned_close = Series[Price](
        timestamps=ctx.close.timestamps[-(len(highest_high)) :],
        values=ctx.close.values[-(len(highest_high)) :],
        symbol=ctx.close.symbol,
        timeframe=ctx.close.timeframe,
    )

    # %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
    # Use 50 when the denominator is zero to avoid divide-by-zero drift.
    k_values = []
    for c_val, h_val, l_val in zip(aligned_close.values, highest_high.values, lowest_low.values, strict=False):
        denom = Decimal(str(h_val)) - Decimal(str(l_val))
        if denom == 0:
            k_values.append(Price("50.0"))
        else:
            num = Decimal(str(c_val)) - Decimal(str(l_val))
            k_values.append(Price((num / denom) * Decimal(100)))
    k_series = Series[Price](
        timestamps=aligned_close.timestamps,
        values=tuple(k_values),
        symbol=aligned_close.symbol,
        timeframe=aligned_close.timeframe,
    )

    # Calculate %D using rolling_mean on %K
    d_series = rolling_mean(SeriesContext(close=k_series), d_period)

    return k_series, d_series


STOCH_K_SPEC = IndicatorSpec(
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
    runtime_binding=RuntimeBindingSpec(kernel_id="stoch_k"),
)


@register(spec=STOCH_K_SPEC)
def stoch_k(ctx: SeriesContext, k_period: int = 14, d_period: int = 3) -> Series[Price]:
    """
    Convenience wrapper that returns only the %K line from stochastic().
    """
    k_series, _ = stochastic(ctx, k_period=k_period, d_period=d_period)
    return k_series


STOCH_D_SPEC = IndicatorSpec(
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
    runtime_binding=RuntimeBindingSpec(kernel_id="stoch_d"),
)


@register(spec=STOCH_D_SPEC)
def stoch_d(ctx: SeriesContext, k_period: int = 14, d_period: int = 3) -> Series[Price]:
    """
    Convenience wrapper that returns only the %D line from stochastic().
    """
    _, d_series = stochastic(ctx, k_period=k_period, d_period=d_period)
    return d_series
