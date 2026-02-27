"""Relative Strength Index (RSI) indicator using primitives."""

from __future__ import annotations

import math

import ta_py

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...registry.schemas import (
    IndicatorSpec,
    InputSlotSpec,
    OutputSpec,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)
from .. import (
    SeriesContext,
    register,
)

RSI_SPEC = IndicatorSpec(
    name="rsi",
    description="Relative Strength Index using Wilder's Smoothing",
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
        "period": ParamSpec(
            name="period",
            type=int,
            default=14,
            required=False,
            description="Lookback period",
            min_value=1,
            max_value=500,
        ),
    },
    outputs={
        "result": OutputSpec(
            name="result",
            type=Series,
            description="RSI values 0-100",
            role="osc_main",
        ),
    },
    semantics=SemanticsSpec(
        required_fields=("close",),
        lookback_params=("period",),
        default_lookback=None,
        input_field="close",
        input_series_param="input_series",
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="rsi"),
    param_aliases={"lookback": "period"},
)


@register(spec=RSI_SPEC)
def rsi(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Relative Strength Index indicator using Wilder's Smoothing.

    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss

    Uses Wilder's Smoothing (Modified Moving Average) for average gains and losses,
    which provides smoother, more accurate RSI values compared to simple moving average.
    """
    if period <= 0:
        raise ValueError("RSI period must be positive")
    close_series = ctx.close
    if close_series is None or len(close_series) == 0:
        # Return empty series with correct meta
        return close_series.__class__(
            timestamps=(),
            values=(),
            symbol=close_series.symbol if close_series is not None else None,
            timeframe=close_series.timeframe if close_series is not None else None,
        )

    out = ta_py.rsi([float(v) for v in close_series.values], period)
    mask = tuple(not math.isnan(v) for v in out)
    return CoreSeries[Price](
        timestamps=close_series.timestamps,
        values=tuple(Price("NaN") if math.isnan(v) else Price(str(v)) for v in out),
        symbol=close_series.symbol,
        timeframe=close_series.timeframe,
        availability_mask=mask,
    )
