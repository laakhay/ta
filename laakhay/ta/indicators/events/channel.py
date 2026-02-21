"""Channel patterns - Detect when price is inside/outside channels."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

from ...core import Series
from ...core.series import align_series
from ...core.types import Price
from ...expr.algebra.operators import Expression
from ...expr.ir.nodes import CallNode as TAIndicatorNode
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
            raise TypeError(f"CallNode evaluated to {type(result)}, expected Series")
        return result
    elif isinstance(value, Series):
        return value
    elif isinstance(value, int | float | Decimal):
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


def _extract_channel_tuple(
    value: Series[Price] | Expression | float | int | Decimal | tuple[Any, ...] | None,
    ctx: SeriesContext,
) -> tuple[Series[Price], Series[Price]] | None:
    """Extract (upper, lower) from a tuple-returning indicator (e.g. bbands)."""
    if isinstance(value, tuple):
        if len(value) < 3:
            return None
        upper = value[0]
        lower = value[2]
        if isinstance(upper, Series) and isinstance(lower, Series):
            return cast(Series[Price], upper), cast(Series[Price], lower)
        return None

    if not isinstance(value, Expression | TAIndicatorNode):
        return None

    base_series = _select(ctx)
    context_dict: dict[str, Series[Price]] = {}
    for field_name in ctx.available_series:
        series = getattr(ctx, field_name)
        if len(series) != len(base_series):
            try:
                _, aligned_series = align_series(base_series, series, how="inner")
                context_dict[field_name] = aligned_series
            except ValueError:
                context_dict[field_name] = series
        else:
            context_dict[field_name] = series

    result = value.evaluate(context_dict)
    if not isinstance(result, tuple) or len(result) < 3:
        return None
    upper = result[0]
    lower = result[2]
    if not isinstance(upper, Series) or not isinstance(lower, Series):
        return None
    return cast(Series[Price], upper), cast(Series[Price], lower)


def _align_price_upper_lower(
    price_series: Series[Price],
    upper_series: Series[Price],
    lower_series: Series[Price],
) -> tuple[Series[Price], Series[Price], Series[Price]] | None:
    """Align price/upper/lower against the same timestamp set."""
    try:
        price_aligned, upper_aligned = align_series(price_series, upper_series, how="inner")
        price_aligned, lower_aligned = align_series(price_aligned, lower_series, how="inner")
        price_aligned, upper_aligned = align_series(price_aligned, upper_aligned, how="inner")
    except ValueError:
        return None
    return price_aligned, upper_aligned, lower_aligned


@register(
    "in_channel",
    aliases=["in"],
    description="Detect when price is inside channel (between upper and lower bounds)",
)
def in_channel(
    ctx: SeriesContext,
    price: Series[Price] | Expression | None = None,
    upper: Series[Price] | Expression | float | int | Decimal | None = None,
    lower: Series[Price] | Expression | float | int | Decimal | None = None,
) -> Series[bool]:
    """
    Detect when price is between upper and lower bounds.

    Logic: (price >= lower) and (price <= upper)

    Args:
        ctx: Series context (used if price/upper/lower not provided)
        price: Price series (defaults to ctx.price or ctx.close)
        upper: Upper bound series or scalar
        lower: Lower bound series or scalar

    Returns:
        Boolean series where True indicates price is inside channel

    Examples:
        # Price inside Bollinger Bands
        in_channel(close, bb(20, 2).upper, bb(20, 2).lower)

        # Price in range
        in_channel(close, 51000, 49000)
    """
    channel_bounds = _extract_channel_tuple(price, ctx) if upper is None and lower is None else None

    if channel_bounds is not None:
        upper_series, lower_series = channel_bounds
        price_series = _extract_series(None, ctx, reference_series=upper_series)
    else:
        price_series = _extract_series(price, ctx)
        upper_series = _extract_series(upper, ctx, reference_series=price_series)
        lower_series = _extract_series(lower, ctx, reference_series=price_series)

    if len(price_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=price_series.symbol, timeframe=price_series.timeframe)

    aligned = _align_price_upper_lower(price_series, upper_series, lower_series)
    if aligned is None:
        return Series[bool](timestamps=(), values=(), symbol=price_series.symbol, timeframe=price_series.timeframe)
    price_aligned, upper_aligned, lower_aligned = aligned

    # Check: price >= lower AND price <= upper
    result_values = tuple(
        (price_aligned.values[i] >= lower_aligned.values[i]) and (price_aligned.values[i] <= upper_aligned.values[i])
        for i in range(len(price_aligned))
    )

    return Series[bool](
        timestamps=price_aligned.timestamps,
        values=result_values,
        symbol=price_aligned.symbol,
        timeframe=price_aligned.timeframe,
    )


@register("out", description="Detect when price is outside channel (above upper or below lower)")
def out(
    ctx: SeriesContext,
    price: Series[Price] | Expression | None = None,
    upper: Series[Price] | Expression | float | int | Decimal | None = None,
    lower: Series[Price] | Expression | float | int | Decimal | None = None,
) -> Series[bool]:
    """
    Detect when price is outside the channel (above upper or below lower).

    Logic: (price > upper) or (price < lower)

    Args:
        ctx: Series context (used if price/upper/lower not provided)
        price: Price series (defaults to ctx.price or ctx.close)
        upper: Upper bound series or scalar
        lower: Lower bound series or scalar

    Returns:
        Boolean series where True indicates price is outside channel

    Examples:
        # Price outside Bollinger Bands
        out(close, bb(20, 2).upper, bb(20, 2).lower)
    """
    channel_bounds = _extract_channel_tuple(price, ctx) if upper is None and lower is None else None

    if channel_bounds is not None:
        upper_series, lower_series = channel_bounds
        price_series = _extract_series(None, ctx, reference_series=upper_series)
    else:
        price_series = _extract_series(price, ctx)
        upper_series = _extract_series(upper, ctx, reference_series=price_series)
        lower_series = _extract_series(lower, ctx, reference_series=price_series)

    if len(price_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=price_series.symbol, timeframe=price_series.timeframe)

    aligned = _align_price_upper_lower(price_series, upper_series, lower_series)
    if aligned is None:
        return Series[bool](timestamps=(), values=(), symbol=price_series.symbol, timeframe=price_series.timeframe)
    price_aligned, upper_aligned, lower_aligned = aligned

    # Check: price > upper OR price < lower
    result_values = tuple(
        (price_aligned.values[i] > upper_aligned.values[i]) or (price_aligned.values[i] < lower_aligned.values[i])
        for i in range(len(price_aligned))
    )

    return Series[bool](
        timestamps=price_aligned.timestamps,
        values=result_values,
        symbol=price_aligned.symbol,
        timeframe=price_aligned.timeframe,
    )


@register("enter", description="Detect when price enters channel (was outside, now inside)")
def enter(
    ctx: SeriesContext,
    price: Series[Price] | Expression | None = None,
    upper: Series[Price] | Expression | float | int | Decimal | None = None,
    lower: Series[Price] | Expression | float | int | Decimal | None = None,
) -> Series[bool]:
    """
    Detect when price enters the channel (was outside, now inside).

    Logic: in_channel(price, upper, lower) and out(shift(price, 1), upper, lower)

    Args:
        ctx: Series context (used if price/upper/lower not provided)
        price: Price series (defaults to ctx.price or ctx.close)
        upper: Upper bound series or scalar
        lower: Lower bound series or scalar

    Returns:
        Boolean series where True indicates price entered channel

    Examples:
        # Price enters Bollinger Bands
        enter(close, bb(20, 2).upper, bb(20, 2).lower)
    """
    channel_bounds = _extract_channel_tuple(price, ctx) if upper is None and lower is None else None

    if channel_bounds is not None:
        upper_series, lower_series = channel_bounds
        price_series = _extract_series(None, ctx, reference_series=upper_series)
    else:
        price_series = _extract_series(price, ctx)
        upper_series = _extract_series(upper, ctx, reference_series=price_series)
        lower_series = _extract_series(lower, ctx, reference_series=price_series)

    if len(price_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=price_series.symbol, timeframe=price_series.timeframe)

    if len(price_series) < 2:
        # Need at least 2 points for entry detection
        return Series[bool](
            timestamps=price_series.timestamps,
            values=tuple(False for _ in price_series.values),
            symbol=price_series.symbol,
            timeframe=price_series.timeframe,
        )

    aligned = _align_price_upper_lower(price_series, upper_series, lower_series)
    if aligned is None:
        return Series[bool](
            timestamps=price_series.timestamps,
            values=tuple(False for _ in price_series.values),
            symbol=price_series.symbol,
            timeframe=price_series.timeframe,
        )
    price_aligned, upper_aligned, lower_aligned = aligned

    # Build result: first value is always False (no previous)
    result_values: list[bool] = [False]
    result_timestamps: list = [price_aligned.timestamps[0]]

    # Check entries starting from index 1
    for i in range(1, len(price_aligned)):
        price_curr = price_aligned.values[i]
        upper_curr = upper_aligned.values[i]
        lower_curr = lower_aligned.values[i]

        price_prev = price_aligned.values[i - 1]
        upper_prev = upper_aligned.values[i - 1]
        lower_prev = lower_aligned.values[i - 1]

        # Current: inside channel
        currently_in = (price_curr >= lower_curr) and (price_curr <= upper_curr)
        # Previous: outside channel
        previously_out = (price_prev > upper_prev) or (price_prev < lower_prev)

        # Entry: currently in AND previously out
        entered = currently_in and previously_out

        result_values.append(entered)
        result_timestamps.append(price_aligned.timestamps[i])

    return Series[bool](
        timestamps=tuple(result_timestamps),
        values=tuple(result_values),
        symbol=price_aligned.symbol,
        timeframe=price_aligned.timeframe,
    )


@register("exit", description="Detect when price exits channel (was inside, now outside)")
def exit(
    ctx: SeriesContext,
    price: Series[Price] | Expression | None = None,
    upper: Series[Price] | Expression | float | int | Decimal | None = None,
    lower: Series[Price] | Expression | float | int | Decimal | None = None,
) -> Series[bool]:
    """
    Detect when price exits the channel (was inside, now outside).

    Logic: out(price, upper, lower) and in_channel(shift(price, 1), upper, lower)

    Args:
        ctx: Series context (used if price/upper/lower not provided)
        price: Price series (defaults to ctx.price or ctx.close)
        upper: Upper bound series or scalar
        lower: Lower bound series or scalar

    Returns:
        Boolean series where True indicates price exited channel

    Examples:
        # Price exits Bollinger Bands
        exit(close, bb(20, 2).upper, bb(20, 2).lower)
    """
    channel_bounds = _extract_channel_tuple(price, ctx) if upper is None and lower is None else None

    if channel_bounds is not None:
        upper_series, lower_series = channel_bounds
        price_series = _extract_series(None, ctx, reference_series=upper_series)
    else:
        price_series = _extract_series(price, ctx)
        upper_series = _extract_series(upper, ctx, reference_series=price_series)
        lower_series = _extract_series(lower, ctx, reference_series=price_series)

    if len(price_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=price_series.symbol, timeframe=price_series.timeframe)

    if len(price_series) < 2:
        return Series[bool](
            timestamps=price_series.timestamps,
            values=tuple(False for _ in price_series.values),
            symbol=price_series.symbol,
            timeframe=price_series.timeframe,
        )

    aligned = _align_price_upper_lower(price_series, upper_series, lower_series)
    if aligned is None:
        return Series[bool](
            timestamps=price_series.timestamps,
            values=tuple(False for _ in price_series.values),
            symbol=price_series.symbol,
            timeframe=price_series.timeframe,
        )
    price_aligned, upper_aligned, lower_aligned = aligned

    # Build result: first value is always False (no previous)
    result_values: list[bool] = [False]
    result_timestamps: list = [price_aligned.timestamps[0]]

    # Check exits starting from index 1
    for i in range(1, len(price_aligned)):
        price_curr = price_aligned.values[i]
        upper_curr = upper_aligned.values[i]
        lower_curr = lower_aligned.values[i]

        price_prev = price_aligned.values[i - 1]
        upper_prev = upper_aligned.values[i - 1]
        lower_prev = lower_aligned.values[i - 1]

        # Current: outside channel
        currently_out = (price_curr > upper_curr) or (price_curr < lower_curr)
        # Previous: inside channel
        previously_in = (price_prev >= lower_prev) and (price_prev <= upper_prev)

        # Exit: currently out AND previously in
        exited = currently_out and previously_in

        result_values.append(exited)
        result_timestamps.append(price_aligned.timestamps[i])

    return Series[bool](
        timestamps=tuple(result_timestamps),
        values=tuple(result_values),
        symbol=price_aligned.symbol,
        timeframe=price_aligned.timeframe,
    )
