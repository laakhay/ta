"""Commodity Channel Index (CCI) indicator implementation."""

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
    SemanticsSpec,
)
from .._utils import results_to_series

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

    h = [float(v) for v in ctx.high.values]
    l = [float(v) for v in ctx.low.values]
    c = [float(v) for v in ctx.close.values]

    out_vals = ta_py.cci(h, l, c, period)

    return results_to_series(out_vals, ctx.close)
