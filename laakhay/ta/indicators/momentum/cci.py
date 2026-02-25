"""Commodity Channel Index (CCI) indicator implementation."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
from ...core.types import Price
from ...primitives.elementwise_ops import absolute_value
from ...primitives.rolling_ops import rolling_mean
from ...primitives.select import select
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)

CCI_SPEC = IndicatorSpec(
    name="cci",
    description="Commodity Channel Index",
    params={"period": ParamSpec(name="period", type=int, default=20, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="CCI values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("period",),
    ),
)


@register(spec=CCI_SPEC)
def cci(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """
    Commodity Channel Index (CCI) indicator.

    CCI = (Typical Price - SMA) / (0.015 * Mean Deviation)
    """
    if period <= 0:
        raise ValueError("CCI period must be positive")

    tp = select(ctx, "typical_price")
    sma = rolling_mean(ctx, period, field="typical_price")

    # Mean Deviation: sum(abs(tp - sma)) / period
    diff = tp - sma
    abs_diff = absolute_value(SeriesContext(close=diff))

    # We can use rolling_mean on abs_diff to get mean deviation
    # But rolling_mean expects a SeriesContext.
    # Let's create a temporary context.
    md_ctx = SeriesContext(close=abs_diff)
    mean_deviation = rolling_mean(md_ctx, period)

    # CCI Calculation
    # Note: 0.015 is the constant used by Lambert to ensure 70-80% of values are between -100 and +100
    denom = mean_deviation * Decimal("0.015")

    # Avoid division by zero
    # We'll use a small epsilon or just let it handle it via Series __truediv__
    # If mean_deviation is 0, CCI is effectively 0 (or undefined)
    # Safe division for CCI
    res_values = []
    num_vals = (tp - sma).values
    den_vals = denom.values
    for i in range(len(num_vals)):
        d = Decimal(str(den_vals[i]))
        if d == 0:
            res_values.append(Decimal(0))
        else:
            res_values.append(Decimal(str(num_vals[i])) / d)

    return Series[Price](
        timestamps=tp.timestamps, values=tuple(Price(v) for v in res_values), symbol=tp.symbol, timeframe=tp.timeframe
    )
