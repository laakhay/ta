"""Chande Momentum Oscillator (CMO) implementation."""

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

CMO_SPEC = IndicatorSpec(
    name="cmo",
    description="Chande Momentum Oscillator",
    params={"period": ParamSpec(name="period", type=int, default=14, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="CMO values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("close",),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="cmo"),
)


@register(spec=CMO_SPEC)
def cmo(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Chande Momentum Oscillator.

    CMO = 100 * (Sum(Gains, n) - Sum(Losses, n)) / (Sum(Gains, n) + Sum(Losses, n))
    """
    if period <= 0:
        raise ValueError("CMO period must be positive")
    out = ta_py.cmo([float(v) for v in ctx.close.values], period)
    return results_to_series(out, ctx.close, value_class=Price)
