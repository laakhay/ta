"""Rate of Change (ROC) indicator implementation."""

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

ROC_SPEC = IndicatorSpec(
    name="roc",
    description="Rate of Change",
    params={"period": ParamSpec(name="period", type=int, default=12, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="ROC values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("close",),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="roc"),
)


@register(spec=ROC_SPEC)
def roc(ctx: SeriesContext, period: int = 12) -> Series[Price]:
    """
    Rate of Change (ROC) indicator.

    ROC = ((Current Close - Close n-periods ago) / Close n-periods ago) * 100
    """
    if period <= 0:
        raise ValueError("ROC period must be positive")

    out = ta_py.roc([float(v) for v in ctx.close.values], period)
    return results_to_series(out, ctx.close, value_class=Price)
