"""Crossing patterns - Detect when series cross each other."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import ta_py

from ...core import Series
from ...core.series import align_series
from ...core.types import Price
from ...indicators._input_resolver import resolve_series_input
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    InputSlotSpec,
    OutputSpec,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)


def _bool_values_to_series(values: list[bool], template: Series[Price]) -> Series[bool]:
    return Series[bool](
        timestamps=template.timestamps,
        values=tuple(values),
        symbol=template.symbol,
        timeframe=template.timeframe,
    )

CROSSUP_SPEC = IndicatorSpec(
    name="crossup",
    description="Detect when series a crosses above series b",
    inputs=(InputSlotSpec(name="a", required=False, default_source="ohlcv", default_field="close"),),
    params={
        "a": ParamSpec(name="a", type=object, default=None, required=False),
        "b": ParamSpec(name="b", type=object, default=None, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Cross above events", role="line")},
    semantics=SemanticsSpec(required_fields=("close",), input_field="close", input_series_param="a"),
    runtime_binding=RuntimeBindingSpec(kernel_id="crossup"),
)


@register(spec=CROSSUP_SPEC)
def crossup(
    ctx: SeriesContext,
    a: Series[Price] | Any | None = None,
    b: Series[Price] | Any | float | int | Decimal | None = None,
) -> Series[bool]:
    """
    Detect when series a crosses above series b.

    Logic: (a > b) and (shift(a, 1) <= shift(b, 1))

    Args:
        ctx: Series context (used if a/b not provided)
        a: First series (defaults to ctx.price or ctx.close)
        b: Second series or scalar value (defaults to ctx.price or ctx.close if a not provided)

    Returns:
        Boolean series where True indicates a cross above event

    Examples:
        # Golden cross: SMA(20) crosses above SMA(50)
        crossup(sma(20), sma(50))

        # Price crosses above resistance
        crossup(close, sma(200))

        # RSI crosses above 70 (overbought)
        crossup(rsi(14), 70)
    """
    # Extract series (Expression resolved via _input_resolver boundary)
    a_series = resolve_series_input(a, ctx)
    b_series = resolve_series_input(b, ctx, reference_series=a_series)

    # Handle empty series
    if len(a_series) == 0 or len(b_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)

    # Align series to common timestamps
    try:
        a_aligned, b_aligned = align_series(a_series, b_series, how="inner")
    except ValueError:
        # No common timestamps
        return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)

    if len(a_aligned) < 2:
        # Need at least 2 points for crossing detection
        return Series[bool](
            timestamps=a_aligned.timestamps,
            values=tuple(False for _ in a_aligned.values),
            symbol=a_aligned.symbol,
            timeframe=a_aligned.timeframe,
        )

    if hasattr(ta_py, "crossup"):
        out = ta_py.crossup(
            [float(v) for v in a_aligned.values],
            [float(v) for v in b_aligned.values],
        )
        return _bool_values_to_series(out, a_aligned)

    # Build result: first value is always False (no previous to compare)
    result_values: list[bool] = [False]
    result_timestamps: list = [a_aligned.timestamps[0]]

    # Check crossings starting from index 1
    # We compare current values with previous values directly
    for i in range(1, len(a_aligned)):
        a_curr = a_aligned.values[i]
        b_curr = b_aligned.values[i]
        a_prev = a_aligned.values[i - 1]
        b_prev = b_aligned.values[i - 1]

        # Cross above: current a > b AND previous a <= b
        crossed = (a_curr > b_curr) and (a_prev <= b_prev)

        result_values.append(crossed)
        result_timestamps.append(a_aligned.timestamps[i])

    return Series[bool](
        timestamps=tuple(result_timestamps),
        values=tuple(result_values),
        symbol=a_aligned.symbol,
        timeframe=a_aligned.timeframe,
    )


CROSSDOWN_SPEC = IndicatorSpec(
    name="crossdown",
    description="Detect when series a crosses below series b",
    inputs=(InputSlotSpec(name="a", required=False, default_source="ohlcv", default_field="close"),),
    params={
        "a": ParamSpec(name="a", type=object, default=None, required=False),
        "b": ParamSpec(name="b", type=object, default=None, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Cross below events", role="line")},
    semantics=SemanticsSpec(required_fields=("close",), input_field="close", input_series_param="a"),
    runtime_binding=RuntimeBindingSpec(kernel_id="crossdown"),
)


@register(spec=CROSSDOWN_SPEC)
def crossdown(
    ctx: SeriesContext,
    a: Series[Price] | Any | None = None,
    b: Series[Price] | Any | float | int | Decimal | None = None,
) -> Series[bool]:
    """
    Detect when series a crosses below series b.

    Logic: (a < b) and (shift(a, 1) >= shift(b, 1))

    Args:
        ctx: Series context (used if a/b not provided)
        a: First series (defaults to ctx.price or ctx.close)
        b: Second series or scalar value (defaults to ctx.price or ctx.close if a not provided)

    Returns:
        Boolean series where True indicates a cross below event

    Examples:
        # Death cross: SMA(20) crosses below SMA(50)
        crossdown(sma(20), sma(50))

        # Price crosses below support
        crossdown(close, sma(200))

        # RSI crosses below 30 (oversold)
        crossdown(rsi(14), 30)
    """
    # Extract series (Expression resolved via _input_resolver boundary)
    a_series = resolve_series_input(a, ctx)
    b_series = resolve_series_input(b, ctx, reference_series=a_series)

    if len(a_series) == 0 or len(b_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)

    try:
        a_aligned, b_aligned = align_series(a_series, b_series, how="inner")
    except ValueError:
        return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)

    if len(a_aligned) < 2:
        return Series[bool](
            timestamps=a_aligned.timestamps,
            values=tuple(False for _ in a_aligned.values),
            symbol=a_aligned.symbol,
            timeframe=a_aligned.timeframe,
        )

    if hasattr(ta_py, "crossdown"):
        out = ta_py.crossdown(
            [float(v) for v in a_aligned.values],
            [float(v) for v in b_aligned.values],
        )
        return _bool_values_to_series(out, a_aligned)

    result_values: list[bool] = [False]
    result_timestamps: list = [a_aligned.timestamps[0]]

    for i in range(1, len(a_aligned)):
        a_curr = a_aligned.values[i]
        b_curr = b_aligned.values[i]
        a_prev = a_aligned.values[i - 1]
        b_prev = b_aligned.values[i - 1]

        # Cross below: current a < b AND previous a >= b
        crossed = (a_curr < b_curr) and (a_prev >= b_prev)

        result_values.append(crossed)
        result_timestamps.append(a_aligned.timestamps[i])

    return Series[bool](
        timestamps=tuple(result_timestamps),
        values=tuple(result_values),
        symbol=a_aligned.symbol,
        timeframe=a_aligned.timeframe,
    )


CROSS_SPEC = IndicatorSpec(
    name="cross",
    description="Detect when series a crosses series b in either direction",
    inputs=(InputSlotSpec(name="a", required=False, default_source="ohlcv", default_field="close"),),
    params={
        "a": ParamSpec(name="a", type=object, default=None, required=False),
        "b": ParamSpec(name="b", type=object, default=None, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Any cross events", role="line")},
    semantics=SemanticsSpec(required_fields=("close",), input_field="close", input_series_param="a"),
    runtime_binding=RuntimeBindingSpec(kernel_id="cross"),
)


@register(spec=CROSS_SPEC)
def cross(
    ctx: SeriesContext,
    a: Series[Price] | Any | None = None,
    b: Series[Price] | Any | float | int | Decimal | None = None,
) -> Series[bool]:
    """
    Detect when series a crosses series b in either direction.

    Logic: crossup(a, b) or crossdown(a, b)

    Args:
        ctx: Series context (used if a/b not provided)
        a: First series (defaults to ctx.price or ctx.close)
        b: Second series or scalar value (defaults to ctx.price or ctx.close if a not provided)

    Returns:
        Boolean series where True indicates any crossing event

    Examples:
        # Any crossing between two SMAs
        cross(sma(20), sma(50))
    """
    # Get crossup and crossdown events
    if hasattr(ta_py, "cross"):
        a_series = resolve_series_input(a, ctx)
        b_series = resolve_series_input(b, ctx, reference_series=a_series)
        if len(a_series) == 0 or len(b_series) == 0:
            return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)
        try:
            a_aligned, b_aligned = align_series(a_series, b_series, how="inner")
        except ValueError:
            return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)
        out = ta_py.cross(
            [float(v) for v in a_aligned.values],
            [float(v) for v in b_aligned.values],
        )
        return _bool_values_to_series(out, a_aligned)

    # Fallback path
    up_events = crossup(ctx, a, b)
    down_events = crossdown(ctx, a, b)

    # Combine: True if either crossup or crossdown is True
    if len(up_events) == 0:
        return down_events
    if len(down_events) == 0:
        return up_events

    # Align and combine boolean series
    try:
        up_aligned, down_aligned = align_series(up_events, down_events, how="inner")
    except ValueError:
        # No common timestamps - return the non-empty one or empty
        return up_events if len(up_events) > 0 else down_events

    # Combine: True if either is True
    combined_values = tuple(up_aligned.values[i] or down_aligned.values[i] for i in range(len(up_aligned)))

    return Series[bool](
        timestamps=up_aligned.timestamps,
        values=combined_values,
        symbol=up_aligned.symbol,
        timeframe=up_aligned.timeframe,
    )
