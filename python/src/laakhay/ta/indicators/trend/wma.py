"""Weighted Moving Average (WMA) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...primitives.rolling_ops import rolling_wma
from ...primitives.select import _select_field
from ...registry.schemas import (
    IndicatorSpec,
    InputSlotSpec,
    OutputSpec,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)
from .. import Price, SeriesContext, register

WMA_SPEC = IndicatorSpec(
    name="wma",
    description="Weighted Moving Average over a price series",
    inputs=(
        InputSlotSpec(
            name="input_series",
            description="Price series (defaults to close)",
            required=False,
            default_source="ohlcv",
            default_field="close",
        ),
    ),
    params={
        "period": ParamSpec(name="period", type=int, default=14, required=False),
        "source": ParamSpec(name="source", type=str, default=None, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="WMA values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("close",),
        lookback_params=("period",),
        input_field="close",
        input_series_param="input_series",
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="wma"),
    param_aliases={"lookback": "period"},
)


@register(spec=WMA_SPEC)
def wma(ctx: SeriesContext, period: int = 14, source: str | None = None) -> Series[Price]:
    """
    Weighted Moving Average using rolling_wma primitive.

    Args:
        ctx: Series context containing price/volume data
        period: Number of periods for the moving average
        source: Optional field name to use as source (e.g., 'close', 'high', 'low').
    """
    if source:
        selected_series = _select_field(ctx, source)
        new_ctx = SeriesContext(price=selected_series)
        return rolling_wma(new_ctx, period)
    return rolling_wma(ctx, period)
