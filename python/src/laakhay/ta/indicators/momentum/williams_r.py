"""Williams %R indicator implementation."""

from __future__ import annotations

import ta_py

from ...core import Series
from ...core.types import Price
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

    out = ta_py.williams_r(
        [float(v) for v in ctx.high.values],
        [float(v) for v in ctx.low.values],
        [float(v) for v in ctx.close.values],
        period,
    )
    return results_to_series(out, ctx.close, value_class=Price)
