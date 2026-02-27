"""Average True Range (ATR) indicator using primitives."""

from __future__ import annotations

import math

import ta_py

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...primitives.elementwise_ops import true_range
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

    # Calculate True Range using primitive
    tr_series = true_range(ctx)

    out = ta_py.atr_from_tr([float(v) for v in tr_series.values], period)
    mask = tuple(not math.isnan(v) for v in out)
    return CoreSeries[Price](
        timestamps=tr_series.timestamps,
        values=tuple(Price("NaN") if math.isnan(v) else Price(str(v)) for v in out),
        symbol=tr_series.symbol,
        timeframe=tr_series.timeframe,
        availability_mask=mask,
    )
