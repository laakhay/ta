"""Fisher Transform indicator implementation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Tuple

from ...core import Series
from ...core.series import Series as CoreSeries
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


@dataclass
class FisherState:
    prev_value: Decimal
    prev_fisher: Decimal


class FisherKernel:
    """Kernel for Fisher Transform smoothing."""

    def initialize(self, xs, **params):
        return FisherState(prev_value=Decimal(0), prev_fisher=Decimal(0))

    def step(self, state: FisherState, x: Decimal, **params: Any) -> Tuple[FisherState, Decimal]:
        if x.is_nan():
            return state, Decimal("NaN")
        # x is the normalized price -0.5 to 0.5
        # value = 0.66 * x + 0.67 * prev_value
        # value clamped to -0.999 to 0.999 to avoid math errors in ln
        value = Decimal("0.66") * x + Decimal("0.67") * state.prev_value
        if value > Decimal("0.999"):
            value = Decimal("0.999")
        if value < Decimal("-0.999"):
            value = Decimal("-0.999")

        # fisher = 0.5 * ln((1 + value) / (1 - value)) + 0.5 * prev_fisher
        v_f = float(value)
        f_val = 0.5 * math.log((1 + v_f) / (1 - v_f))
        fisher = Decimal(str(f_val)) + Decimal("0.5") * state.prev_fisher

        return FisherState(prev_value=value, prev_fisher=fisher), fisher


FISHER_SPEC = IndicatorSpec(
    name="fisher",
    description="Fisher Transform",
    params={"period": ParamSpec(name="period", type=int, default=9, required=False)},
    outputs={
        "fisher": OutputSpec(name="fisher", type=Series, description="Fisher Transform", role="line"),
        "signal": OutputSpec(name="signal", type=Series, description="Signal Line (Fisher delayed by 1)", role="line"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low"),
        lookback_params=("period",),
    ),
)


@register(spec=FISHER_SPEC)
def fisher(ctx: SeriesContext, period: int = 9) -> tuple[Series[Price], Series[Price]]:
    """
    Fisher Transform indicator.
    """
    if period <= 0:
        raise ValueError("Fisher period must be positive")

    # HL2 = (high + low) / 2
    hl2 = (ctx.high + ctx.low) / Decimal("2")

    # Max/Min over period
    h_max = rolling_max(SeriesContext(close=hl2), period=period)
    l_min = rolling_min(SeriesContext(close=hl2), period=period)

    n = len(hl2)
    # Normalized price x = (hl2 - l_min) / (h_max - l_min) - 0.5
    # Then smoothed with kernel

    kernel = FisherKernel()
    state = kernel.initialize([])

    fisher_vals = []

    for i in range(n):
        diff = Decimal(str(h_max.values[i] - l_min.values[i]))
        if diff == 0:
            x = Decimal(0)
        else:
            x = (Decimal(str(hl2.values[i])) - Decimal(str(l_min.values[i]))) / diff - Decimal("0.5")

        state, f_val = kernel.step(state, x)
        fisher_vals.append(f_val)

    fisher_series = CoreSeries[Price](
        timestamps=hl2.timestamps,
        values=tuple(Price(v) for v in fisher_vals),
        symbol=hl2.symbol,
        timeframe=hl2.timeframe,
    )

    # Signal is fisher delayed by 1
    signal_vals = [Decimal(0)] + list(fisher_vals[:-1])
    signal_series = CoreSeries[Price](
        timestamps=hl2.timestamps,
        values=tuple(Price(v) for v in signal_vals),
        symbol=hl2.symbol,
        timeframe=hl2.timeframe,
    )

    return fisher_series, signal_series
