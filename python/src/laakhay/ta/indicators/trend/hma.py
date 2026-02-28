"""Hull Moving Average (HMA) indicator implementation."""

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

HMA_SPEC = IndicatorSpec(
    name="hma",
    description="Hull Moving Average (fast, lag-reduced)",
    params={"period": ParamSpec(name="period", type=int, default=14, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="HMA values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("close",),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="hma"),
)


@register(spec=HMA_SPEC)
def hma(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """Hull Moving Average (HMA) implementation."""
    if period <= 0:
        raise ValueError("HMA period must be positive")
    result = ta_py.hma([float(v) for v in ctx.close.values], period)
    return results_to_series(result, ctx.close, value_class=Price)
