"""Chaikin Money Flow (CMF) indicator implementation."""

from __future__ import annotations

import math

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)
import ta_py

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

    h, l, c, v = ctx.high, ctx.low, ctx.close, ctx.volume
    out = ta_py.cmf(
        [float(x) for x in h.values],
        [float(x) for x in l.values],
        [float(x) for x in c.values],
        [float(x) for x in v.values],
        period,
    )
    return CoreSeries[Price](
        timestamps=c.timestamps,
        values=tuple(Price("NaN") if math.isnan(x) else Price(str(x)) for x in out),
        symbol=c.symbol,
        timeframe=c.timeframe,
        availability_mask=tuple(not math.isnan(x) for x in out),
    )
