"""Williams %R indicator implementation."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
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

WILLIAMS_R_SPEC = IndicatorSpec(
    name="williams_r",
    description="Williams %R",
    params={"period": ParamSpec(name="period", type=int, default=14, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="Williams %R values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("period",),
    ),
)


@register(spec=WILLIAMS_R_SPEC)
def williams_r(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Williams %R indicator.

    %R = (Highest High - Close) / (Highest High - Lowest Low) * -100
    """
    if period <= 0:
        raise ValueError("Williams %R period must be positive")

    hh = rolling_max(ctx, period, field="high")
    ll = rolling_min(ctx, period, field="low")
    c = ctx.close

    range_hhll = hh - ll

    # Safe division
    res_values = []
    for i in range(len(hh)):
        r = Decimal(str(range_hhll.values[i]))
        if r == 0:
            res_values.append(Decimal(0))
        else:
            res_values.append((Decimal(str(hh.values[i])) - Decimal(str(c.values[i]))) / r * Decimal("-100"))

    return Series[Price](
        timestamps=hh.timestamps, values=tuple(Price(v) for v in res_values), symbol=hh.symbol, timeframe=hh.timeframe
    )
