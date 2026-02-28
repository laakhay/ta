"""Exponential Moving Average (EMA) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...primitives.rolling_ops import rolling_ema
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

EMA_SPEC = IndicatorSpec(
    name="ema",
    description="Exponential Moving Average over a price series",
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
        "period": ParamSpec(name="period", type=int, default=20, required=False),
        "source": ParamSpec(name="source", type=str, default=None, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="EMA values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("close",),
        lookback_params=("period",),
        input_field="close",
        input_series_param="input_series",
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="ema"),
    param_aliases={"lookback": "period"},
)


@register(spec=EMA_SPEC)
def ema(ctx: SeriesContext, period: int = 20, source: str | None = None) -> Series[Price]:
    """
    Exponential Moving Average using rolling_ema primitive.

    This implementation uses the rolling_ema primitive for consistency
    and maintainability.

    Args:
        ctx: Series context containing price/volume data
        period: Number of periods for the moving average
        source: Optional field name to use as source (e.g., 'close', 'volume', 'high', 'low', 'open').
                Defaults to 'close' or 'price' if not specified.
    """
    if source:
        selected_series = _select_field(ctx, source)
        # Create a new context with the selected series as 'price' for rolling_ema
        new_ctx = SeriesContext(price=selected_series)
        return rolling_ema(new_ctx, period)
    return rolling_ema(ctx, period)
