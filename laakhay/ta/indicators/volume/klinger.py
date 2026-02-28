"""Klinger Oscillator indicator implementation."""

from __future__ import annotations

import math

import ta_py

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...primitives.rolling_ops import rolling_ema
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
    runtime_binding=RuntimeBindingSpec(kernel_id="klinger"),
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

    if hasattr(ta_py, "klinger"):
        klinger_vals, signal_vals = ta_py.klinger(
            [float(x) for x in h.values],
            [float(x) for x in l.values],
            [float(x) for x in c.values],
            [float(x) for x in v.values],
            fast_period,
            slow_period,
            signal_period,
        )
        return (
            results_to_series(klinger_vals, c, value_class=Price),
            results_to_series(signal_vals, c, value_class=Price),
        )

    # Temporary fallback while ta_py upgrades.
    vf_vals = ta_py.klinger_vf([float(x) for x in h.values], [float(x) for x in l.values], [float(x) for x in c.values], [float(x) for x in v.values])
    vf_series = CoreSeries[Price](timestamps=c.timestamps, values=tuple(Price("NaN") if math.isnan(vf) else Price(str(vf)) for vf in vf_vals), symbol=c.symbol, timeframe=c.timeframe)

    # Klinger = EMA(VF, fast) - EMA(VF, slow)
    ema_fast = rolling_ema(SeriesContext(close=vf_series), period=fast_period)
    ema_slow = rolling_ema(SeriesContext(close=vf_series), period=slow_period)

    klinger_series = ema_fast - ema_slow

    # Signal = EMA(Klinger, signal)
    signal_series = rolling_ema(SeriesContext(close=klinger_series), period=signal_period)

    return klinger_series, signal_series
