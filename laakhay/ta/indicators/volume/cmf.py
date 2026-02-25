"""Chaikin Money Flow (CMF) indicator implementation."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
from ...core.types import Price
from ...primitives.rolling_ops import rolling_sum
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)

CMF_SPEC = IndicatorSpec(
    name="cmf",
    description="Chaikin Money Flow",
    params={"period": ParamSpec(name="period", type=int, default=20, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="CMF values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close", "volume"),
        lookback_params=("period",),
    ),
)


@register(spec=CMF_SPEC)
def cmf(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """
    Chaikin Money Flow (CMF) indicator.

    MFM = ((Close - Low) - (High - Close)) / (High - Low)
    MFV = MFM * Volume
    CMF = Rolling Sum (MFV, period) / Rolling Sum (Volume, period)
    """
    if period <= 0:
        raise ValueError("CMF period must be positive")

    h = ctx.high
    l = ctx.low
    c = ctx.close
    v = ctx.volume

    # Money Flow Multiplier
    # Denominator (h - l)
    range_hl = h - l

    # Handling divide by zero where h == l
    # We'll use a series of 0s for the multiplier where range is 0
    numerator = (c - l) - (h - c)

    # We can use a trick: (numerator / range_hl) and then fill NaNs or just use a loop
    # Given Series architecture, a loop or a specialized kernel might be safer for edge cases.
    # However, for simplicity and staying with composition:

    # Let's use a safe division if possible.
    # Actually, let's just use the algebraic form and hope for the best,
    # OR implement it carefully.

    # I'll implement Money Flow Volume via a simple list comprehension for robustness against H=L
    mfv_values = []
    for i in range(len(c)):
        hl = Decimal(str(h.values[i])) - Decimal(str(l.values[i]))
        if hl == 0:
            mfv_values.append(Decimal(0))
        else:
            mfm = (
                (Decimal(str(c.values[i])) - Decimal(str(l.values[i])))
                - (Decimal(str(h.values[i])) - Decimal(str(c.values[i])))
            ) / hl
            mfv_values.append(mfm * Decimal(str(v.values[i])))

    mfv_series = Series[Price](
        timestamps=c.timestamps, values=tuple(Price(val) for val in mfv_values), symbol=c.symbol, timeframe=c.timeframe
    )

    mfv_ctx = SeriesContext(close=mfv_series)
    sum_mfv = rolling_sum(mfv_ctx, period)

    v_ctx = SeriesContext(close=v)
    sum_v = rolling_sum(v_ctx, period)

    # Safe division for CMF
    res_values = []
    for i in range(len(sum_mfv)):
        sv = Decimal(str(sum_v.values[i]))
        if sv == 0:
            res_values.append(Decimal(0))
        else:
            res_values.append(Decimal(str(sum_mfv.values[i])) / sv)

    return Series[Price](
        timestamps=sum_mfv.timestamps,
        values=tuple(Price(v) for v in res_values),
        symbol=sum_mfv.symbol,
        timeframe=sum_mfv.timeframe,
    )
