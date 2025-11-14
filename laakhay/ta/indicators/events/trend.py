"""Trend patterns - Detect rising/falling movements in series."""

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
    value: Series[Price] | Expression | None,
    ctx: SeriesContext,
) -> Series[Price]:
    """Extract a Series from various input types."""
    if value is None:
        return _select(ctx)
    elif isinstance(value, Expression):
        # Convert SeriesContext to dict for Expression.evaluate()
        # Use close as the base context to ensure consistent evaluation
        base_series = _select(ctx)
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
        # Use close as the base context to ensure consistent evaluation
        base_series = _select(ctx)
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
    else:
        raise TypeError(f"Unsupported type for series extraction: {type(value)}")


@register("rising", description="Detect when series is moving up (current > previous)")
def rising(
    ctx: SeriesContext,
    a: Series[Price] | Expression | None = None,
) -> Series[bool]:
    """
    Detect when series a is rising (current > previous).

    Logic: a > shift(a, 1)

    Args:
        ctx: Series context (used if a not provided)
        a: Series to check (defaults to ctx.price or ctx.close)

    Returns:
        Boolean series where True indicates rising movement

    Examples:
        # Price is rising
        rising(close)

        # RSI is rising
        rising(rsi(14))
    """
    a_series = _extract_series(a, ctx)

    if len(a_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)

    if len(a_series) < 2:
        # Need at least 2 points for comparison
        return Series[bool](
            timestamps=a_series.timestamps,
            values=tuple(False for _ in a_series.values),
            symbol=a_series.symbol,
            timeframe=a_series.timeframe,
        )

    # First value is always False (no previous)
    result_values: list[bool] = [False]
    result_timestamps: list = [a_series.timestamps[0]]

    # Check rising: current > previous (direct comparison)
    for i in range(1, len(a_series)):
        is_rising = a_series.values[i] > a_series.values[i - 1]
        result_values.append(is_rising)
        result_timestamps.append(a_series.timestamps[i])

    return Series[bool](
        timestamps=tuple(result_timestamps),
        values=tuple(result_values),
        symbol=a_series.symbol,
        timeframe=a_series.timeframe,
    )


@register("falling", description="Detect when series is moving down (current < previous)")
def falling(
    ctx: SeriesContext,
    a: Series[Price] | Expression | None = None,
) -> Series[bool]:
    """
    Detect when series a is falling (current < previous).

    Logic: a < shift(a, 1)

    Args:
        ctx: Series context (used if a not provided)
        a: Series to check (defaults to ctx.price or ctx.close)

    Returns:
        Boolean series where True indicates falling movement

    Examples:
        # Price is falling
        falling(close)

        # Volume is falling
        falling(volume)
    """
    a_series = _extract_series(a, ctx)

    if len(a_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)

    if len(a_series) < 2:
        return Series[bool](
            timestamps=a_series.timestamps,
            values=tuple(False for _ in a_series.values),
            symbol=a_series.symbol,
            timeframe=a_series.timeframe,
        )

    result_values: list[bool] = [False]
    result_timestamps: list = [a_series.timestamps[0]]

    for i in range(1, len(a_series)):
        is_falling = a_series.values[i] < a_series.values[i - 1]
        result_values.append(is_falling)
        result_timestamps.append(a_series.timestamps[i])

    return Series[bool](
        timestamps=tuple(result_timestamps),
        values=tuple(result_values),
        symbol=a_series.symbol,
        timeframe=a_series.timeframe,
    )


@register("rising_pct", description="Detect when series has risen by at least pct percent")
def rising_pct(
    ctx: SeriesContext,
    a: Series[Price] | Expression | None = None,
    pct: float | int | Decimal = 0,
) -> Series[bool]:
    """
    Detect when series a has risen by at least pct percent.

    Logic: a >= shift(a, 1) * (1 + pct / 100)

    Args:
        ctx: Series context (used if a not provided)
        a: Series to check (defaults to ctx.price or ctx.close)
        pct: Percentage threshold (e.g., 5 for 5%)

    Returns:
        Boolean series where True indicates rise by at least pct%

    Examples:
        # Price rose by 5%
        rising_pct(close, 5)

        # Volume rose by 10%
        rising_pct(volume, 10)
    """
    a_series = _extract_series(a, ctx)

    if len(a_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)

    if len(a_series) < 2:
        return Series[bool](
            timestamps=a_series.timestamps,
            values=tuple(False for _ in a_series.values),
            symbol=a_series.symbol,
            timeframe=a_series.timeframe,
        )

    pct_decimal = Decimal(str(pct))
    multiplier = Decimal("1") + (pct_decimal / Decimal("100"))

    result_values: list[bool] = [False]
    result_timestamps: list = [a_series.timestamps[0]]

    for i in range(1, len(a_series)):
        threshold = a_series.values[i - 1] * multiplier
        is_rising_pct = a_series.values[i] >= threshold
        result_values.append(is_rising_pct)
        result_timestamps.append(a_series.timestamps[i])

    return Series[bool](
        timestamps=tuple(result_timestamps),
        values=tuple(result_values),
        symbol=a_series.symbol,
        timeframe=a_series.timeframe,
    )


@register("falling_pct", description="Detect when series has fallen by at least pct percent")
def falling_pct(
    ctx: SeriesContext,
    a: Series[Price] | Expression | None = None,
    pct: float | int | Decimal = 0,
) -> Series[bool]:
    """
    Detect when series a has fallen by at least pct percent.

    Logic: a <= shift(a, 1) * (1 - pct / 100)

    Args:
        ctx: Series context (used if a not provided)
        a: Series to check (defaults to ctx.price or ctx.close)
        pct: Percentage threshold (e.g., 5 for 5%)

    Returns:
        Boolean series where True indicates fall by at least pct%

    Examples:
        # Price fell by 5%
        falling_pct(close, 5)
    """
    a_series = _extract_series(a, ctx)

    if len(a_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)

    if len(a_series) < 2:
        return Series[bool](
            timestamps=a_series.timestamps,
            values=tuple(False for _ in a_series.values),
            symbol=a_series.symbol,
            timeframe=a_series.timeframe,
        )

    pct_decimal = Decimal(str(pct))
    multiplier = Decimal("1") - (pct_decimal / Decimal("100"))

    result_values: list[bool] = [False]
    result_timestamps: list = [a_series.timestamps[0]]

    for i in range(1, len(a_series)):
        threshold = a_series.values[i - 1] * multiplier
        is_falling_pct = a_series.values[i] <= threshold
        result_values.append(is_falling_pct)
        result_timestamps.append(a_series.timestamps[i])

    return Series[bool](
        timestamps=tuple(result_timestamps),
        values=tuple(result_values),
        symbol=a_series.symbol,
        timeframe=a_series.timeframe,
    )
