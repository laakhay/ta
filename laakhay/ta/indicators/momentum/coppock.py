"""Coppock Curve indicator implementation."""

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

COPPOCK_SPEC = IndicatorSpec(
    name="coppock",
    description="Coppock Curve",
    params={
        "wma_period": ParamSpec(name="wma_period", type=int, default=10, required=False),
        "fast_roc": ParamSpec(name="fast_roc", type=int, default=11, required=False),
        "slow_roc": ParamSpec(name="slow_roc", type=int, default=14, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Coppock Curve values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("close",),
        lookback_params=("wma_period", "fast_roc", "slow_roc"),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="coppock"),
)


@register(spec=COPPOCK_SPEC)
def coppock(
    ctx: SeriesContext,
    wma_period: int = 10,
    fast_roc: int = 11,
    slow_roc: int = 14,
) -> Series[Price]:
    """
    Coppock Curve indicator.

    Coppock Curve = WMA(wma_period) of (ROC(fast_roc) + ROC(slow_roc))
    """
    if wma_period <= 0 or fast_roc <= 0 or slow_roc <= 0:
        raise ValueError("Coppock periods must be positive")

    out = ta_py.coppock(
        [float(v) for v in ctx.close.values],
        wma_period,
        fast_roc,
        slow_roc,
    )
    return results_to_series(out, ctx.close, value_class=Price)
