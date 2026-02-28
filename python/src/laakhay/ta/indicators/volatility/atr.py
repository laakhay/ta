"""Average True Range (ATR) indicator using primitives."""

from __future__ import annotations

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

ATR_SPEC = IndicatorSpec(
    name="atr",
    description="Average True Range indicator",
    params={"period": ParamSpec(name="period", type=int, default=14, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="ATR values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="atr"),
    param_aliases={"lookback": "period"},
)


@register(spec=ATR_SPEC)
def atr(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Average True Range indicator using primitives.

    ATR = Rolling Mean of True Range
    """
    if period <= 0:
        raise ValueError("ATR period must be positive")

    # Validate series lengths before processing
    required_series = ["high", "low", "close"]
    series_lengths = []
    for s in required_series:
        if hasattr(ctx, s) and getattr(ctx, s) is not None:
            series_lengths.append(len(getattr(ctx, s)))

    if len(series_lengths) > 1 and len(set(series_lengths)) > 1:
        raise ValueError("All series must have the same length")

    import ta_py

    from .._utils import results_to_series

    out = ta_py.atr(
        [float(v) for v in ctx.high.values],
        [float(v) for v in ctx.low.values],
        [float(v) for v in ctx.close.values],
        period,
    )
    return results_to_series(out, ctx.close, value_class=Price)
