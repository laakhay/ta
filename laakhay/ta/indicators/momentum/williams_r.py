"""Williams %R indicator implementation."""

from __future__ import annotations

import ta_py
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
    RuntimeBindingSpec,
    SemanticsSpec,
)
from .._utils import results_to_series

WILLIAMS_R_SPEC = IndicatorSpec(
    name="williams_r",
    description="Williams %R",
    params={"period": ParamSpec(name="period", type=int, default=14, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="Williams %R values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="williams_r"),
)


@register(spec=WILLIAMS_R_SPEC)
def williams_r(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Williams %R indicator.

    %R = (Highest High - Close) / (Highest High - Lowest Low) * -100
    """
    if period <= 0:
        raise ValueError("Williams %R period must be positive")

    if hasattr(ta_py, "williams_r"):
        out = ta_py.williams_r(
            [float(v) for v in ctx.high.values],
            [float(v) for v in ctx.low.values],
            [float(v) for v in ctx.close.values],
            period,
        )
        return results_to_series(out, ctx.close, value_class=Price)

    # Temporary fallback while environments upgrade ta_py.
    hh = rolling_max(ctx, period, field="high")
    ll = rolling_min(ctx, period, field="low")
    c = ctx.close
    range_hhll = hh - ll
    res_values = []
    for i in range(len(hh)):
        r = Decimal(str(range_hhll.values[i]))
        if r == 0:
            res_values.append(Decimal(0))
        else:
            res_values.append((Decimal(str(hh.values[i])) - Decimal(str(c.values[i]))) / r * Decimal("-100"))
    return Series[Price](
        timestamps=hh.timestamps,
        values=tuple(Price(v) for v in res_values),
        symbol=hh.symbol,
        timeframe=hh.timeframe,
    )
