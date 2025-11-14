"""Crossing patterns - Detect when series cross each other."""

from __future__ import annotations

from decimal import Decimal

from ...api.handle import IndicatorNode as TAIndicatorNode
from ...core import Series
from ...core.series import align_series
from ...core.types import Price
from ...expr.algebra.operators import Expression
from ...primitives import _select
from ...registry.models import SeriesContext
from ...registry.registry import register


def _extract_series(
    value: Series[Price] | Expression | float | int | Decimal | None,
    ctx: SeriesContext,
    reference_series: Series[Price] | None = None,
) -> Series[Price]:
    """Extract a Series from various input types."""
    if value is None:
        return _select(ctx)
    elif isinstance(value, Expression):
        # Convert SeriesContext to dict for Expression.evaluate()
        # Use the reference series or close as the base context to ensure consistent evaluation
        base_series = reference_series if reference_series is not None else _select(ctx)
        context_dict: dict[str, Series[Price]] = {}
        for field_name in ctx.available_series:
            series = getattr(ctx, field_name)
            # Ensure all context series have the same length as the base series
            # by aligning them (this handles different lookback periods)
            if len(series) != len(base_series):
                try:
                    aligned_base, aligned_series = align_series(base_series, series, how="inner")
                    context_dict[field_name] = aligned_series
                except ValueError:
                    # If alignment fails, use the original series
                    context_dict[field_name] = series
            else:
                context_dict[field_name] = series
        result = value.evaluate(context_dict)
        if not isinstance(result, Series):
            raise TypeError(f"Expression evaluated to {type(result)}, expected Series")
        return result
    elif isinstance(value, TAIndicatorNode):
        # Handle IndicatorNode (internal node from laakhay-ta)
        # Convert SeriesContext to dict for IndicatorNode.evaluate()
        # Use the reference series or close as the base context to ensure consistent evaluation
        base_series = reference_series if reference_series is not None else _select(ctx)
        context_dict: dict[str, Series[Price]] = {}
        for field_name in ctx.available_series:
            series = getattr(ctx, field_name)
            # Ensure all context series have the same length as the base series
            # by aligning them (this handles different lookback periods)
            if len(series) != len(base_series):
                try:
                    aligned_base, aligned_series = align_series(base_series, series, how="inner")
                    context_dict[field_name] = aligned_series
                except ValueError:
                    # If alignment fails, use the original series
                    context_dict[field_name] = series
            else:
                context_dict[field_name] = series
        result = value.evaluate(context_dict)
        if not isinstance(result, Series):
            raise TypeError(f"IndicatorNode evaluated to {type(result)}, expected Series")
        return result
    elif isinstance(value, Series):
        return value
    elif isinstance(value, int | float | Decimal):
        # Convert scalar to series matching reference or context
        if reference_series is not None:
            ref = reference_series
        else:
            ref = _select(ctx)
        return Series[Price](
            timestamps=ref.timestamps,
            values=tuple(Decimal(str(value)) for _ in ref.timestamps),
            symbol=ref.symbol,
            timeframe=ref.timeframe,
        )
    else:
        raise TypeError(f"Unsupported type for series extraction: {type(value)}")


@register("crossup", description="Detect when series a crosses above series b")
def crossup(
    ctx: SeriesContext,
    a: Series[Price] | Expression | None = None,
    b: Series[Price] | Expression | float | int | Decimal | None = None,
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
    # Extract series
    a_series = _extract_series(a, ctx)
    b_series = _extract_series(b, ctx, reference_series=a_series)

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


@register("crossdown", description="Detect when series a crosses below series b")
def crossdown(
    ctx: SeriesContext,
    a: Series[Price] | Expression | None = None,
    b: Series[Price] | Expression | float | int | Decimal | None = None,
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
    # Extract series (same as crossup)
    a_series = _extract_series(a, ctx)
    b_series = _extract_series(b, ctx, reference_series=a_series)

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

    if len(a_aligned) < 2:
        return Series[bool](
            timestamps=a_aligned.timestamps,
            values=tuple(False for _ in a_aligned.values),
            symbol=a_aligned.symbol,
            timeframe=a_aligned.timeframe,
        )

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


@register("cross", description="Detect when series a crosses series b in either direction")
def cross(
    ctx: SeriesContext,
    a: Series[Price] | Expression | None = None,
    b: Series[Price] | Expression | float | int | Decimal | None = None,
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
