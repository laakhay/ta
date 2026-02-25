"""Klinger Oscillator indicator implementation."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...primitives.kernels.klinger import KlingerVFKernel
from ...primitives.rolling_ops import rolling_ema
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)

KLINGER_SPEC = IndicatorSpec(
    name="klinger",
    description="Klinger Oscillator",
    params={
        "fast_period": ParamSpec(name="fast_period", type=int, default=34, required=False),
        "slow_period": ParamSpec(name="slow_period", type=int, default=55, required=False),
        "signal_period": ParamSpec(name="signal_period", type=int, default=13, required=False),
    },
    outputs={
        "klinger": OutputSpec(name="klinger", type=Series, description="Klinger Oscillator", role="line"),
        "signal": OutputSpec(name="signal", type=Series, description="Signal Line", role="line"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close", "volume"),
        lookback_params=("fast_period", "slow_period", "signal_period"),
    ),
)


@register(spec=KLINGER_SPEC)
def klinger(
    ctx: SeriesContext,
    fast_period: int = 34,
    slow_period: int = 55,
    signal_period: int = 13,
) -> tuple[Series[Price], Series[Price]]:
    """
    Klinger Oscillator.
    """
    if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
        raise ValueError("Klinger periods must be positive")

    h, l, c, v = ctx.high, ctx.low, ctx.close, ctx.volume
    n = len(c)
    if n == 0:
        empty = CoreSeries[Price](timestamps=(), values=(), symbol=c.symbol, timeframe=c.timeframe)
        return empty, empty

    # Calculate Volume Force (VF) using kernel
    hlcv_vals = [
        (Decimal(str(h.values[i])), Decimal(str(l.values[i])), Decimal(str(c.values[i])), Decimal(str(v.values[i])))
        for i in range(n)
    ]

    kernel = KlingerVFKernel()
    state = kernel.initialize([])

    vf_vals = []
    for i in range(n):
        state, vf = kernel.step(state, hlcv_vals[i])
        vf_vals.append(vf)

    vf_series = CoreSeries[Price](
        timestamps=c.timestamps, values=tuple(Price(v) for v in vf_vals), symbol=c.symbol, timeframe=c.timeframe
    )

    # Klinger = EMA(VF, fast) - EMA(VF, slow)
    ema_fast = rolling_ema(SeriesContext(close=vf_series), period=fast_period)
    ema_slow = rolling_ema(SeriesContext(close=vf_series), period=slow_period)

    klinger_series = ema_fast - ema_slow

    # Signal = EMA(Klinger, signal)
    signal_series = rolling_ema(SeriesContext(close=klinger_series), period=signal_period)

    return klinger_series, signal_series
