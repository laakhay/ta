"""Rate of Change (ROC) indicator implementation."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
from ...core.types import Price
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)

ROC_SPEC = IndicatorSpec(
    name="roc",
    description="Rate of Change",
    params={"period": ParamSpec(name="period", type=int, default=12, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="ROC values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("close",),
        lookback_params=("period",),
    ),
)


@register(spec=ROC_SPEC)
def roc(ctx: SeriesContext, period: int = 12) -> Series[Price]:
    """
    Rate of Change (ROC) indicator.

    ROC = ((Current Close - Close n-periods ago) / Close n-periods ago) * 100
    """
    if period <= 0:
        raise ValueError("ROC period must be positive")

    c = ctx.close
    c_prev = c.shift(period)

    # Division by zero where c_prev is zero is handled by Series __truediv__
    return ((c - c_prev) / c_prev) * Decimal("100")
