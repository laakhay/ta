"""Chande Momentum Oscillator (CMO) implementation."""

from __future__ import annotations

import ta_py
from decimal import Decimal

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...primitives.rolling_ops import rolling_sum
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

CMO_SPEC = IndicatorSpec(
    name="cmo",
    description="Chande Momentum Oscillator",
    params={"period": ParamSpec(name="period", type=int, default=14, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="CMO values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("close",),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="cmo"),
)


@register(spec=CMO_SPEC)
def cmo(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Chande Momentum Oscillator.

    CMO = 100 * (Sum(Gains, n) - Sum(Losses, n)) / (Sum(Gains, n) + Sum(Losses, n))
    """
    if period <= 0:
        raise ValueError("CMO period must be positive")
    if hasattr(ta_py, "cmo"):
        out = ta_py.cmo([float(v) for v in ctx.close.values], period)
        return results_to_series(out, ctx.close, value_class=Price)

    # Temporary fallback while environments upgrade ta_py.
    close = ctx.close
    n = len(close)
    if n < 2:
        return CoreSeries[Price](
            timestamps=close.timestamps,
            values=tuple(Price(0) for _ in close.values),
            symbol=close.symbol,
            timeframe=close.timeframe,
        )

    gains = [Decimal(0)]
    losses = [Decimal(0)]
    prev_val = Decimal(str(close.values[0]))
    for i in range(1, n):
        curr_val = Decimal(str(close.values[i]))
        if curr_val > prev_val:
            gains.append(curr_val - prev_val)
            losses.append(Decimal(0))
        else:
            gains.append(Decimal(0))
            losses.append(prev_val - curr_val)
        prev_val = curr_val

    gains_series = CoreSeries[Price](
        timestamps=close.timestamps,
        values=tuple(Price(v) for v in gains),
        symbol=close.symbol,
        timeframe=close.timeframe,
    )
    losses_series = CoreSeries[Price](
        timestamps=close.timestamps,
        values=tuple(Price(v) for v in losses),
        symbol=close.symbol,
        timeframe=close.timeframe,
    )
    sum_gains = rolling_sum(SeriesContext(close=gains_series), period=period)
    sum_losses = rolling_sum(SeriesContext(close=losses_series), period=period)

    cmo_vals = []
    for i in range(n):
        sg = Decimal(str(sum_gains.values[i]))
        sl = Decimal(str(sum_losses.values[i]))
        denom = sg + sl
        cmo_vals.append(Decimal(0) if denom == 0 else Decimal("100") * (sg - sl) / denom)

    return CoreSeries[Price](
        timestamps=close.timestamps,
        values=tuple(Price(v) for v in cmo_vals),
        symbol=close.symbol,
        timeframe=close.timeframe,
        availability_mask=sum_gains.availability_mask,
    )
