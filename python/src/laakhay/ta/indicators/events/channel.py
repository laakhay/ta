"""Channel patterns - Detect when price is inside/outside channels."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import ta_py

from ...core import Series
from ...core.series import align_series
from ...core.types import Price
from ...indicators._input_resolver import resolve_channel_tuple, resolve_series_input
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

IN_CHANNEL_SPEC = IndicatorSpec(
    name="in_channel",
    description="Detect when price is inside channel (between upper and lower bounds)",
    aliases=("in",),
    inputs=(InputSlotSpec(name="price", required=False, default_source="ohlcv", default_field="close"),),
    params={
        "price": ParamSpec(name="price", type=object, default=None, required=False),
        "upper": ParamSpec(name="upper", type=object, default=None, required=False),
        "lower": ParamSpec(name="lower", type=object, default=None, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Price inside channel", role="line")},
    semantics=SemanticsSpec(required_fields=("close",), input_field="close", input_series_param="price"),
    runtime_binding=RuntimeBindingSpec(kernel_id="in_channel"),
)


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


def _bool_values_to_series(values: list[bool], template: Series[Price]) -> Series[bool]:
    return Series[bool](
        timestamps=template.timestamps,
        values=tuple(values),
        symbol=template.symbol,
        timeframe=template.timeframe,
    )


@register(spec=IN_CHANNEL_SPEC)
def in_channel(
    ctx: SeriesContext,
    price: Series[Price] | Any | None = None,
    upper: Series[Price] | Any | float | int | Decimal | None = None,
    lower: Series[Price] | Any | float | int | Decimal | None = None,
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
    channel_bounds = resolve_channel_tuple(price, ctx) if upper is None and lower is None else None

    if channel_bounds is not None:
        upper_series, lower_series = channel_bounds
        price_series = resolve_series_input(None, ctx, reference_series=upper_series)
    else:
        price_series = resolve_series_input(price, ctx)
        upper_series = resolve_series_input(upper, ctx, reference_series=price_series)
        lower_series = resolve_series_input(lower, ctx, reference_series=price_series)

    if len(price_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=price_series.symbol, timeframe=price_series.timeframe)

    aligned = _align_price_upper_lower(price_series, upper_series, lower_series)
    if aligned is None:
        return Series[bool](timestamps=(), values=(), symbol=price_series.symbol, timeframe=price_series.timeframe)
    price_aligned, upper_aligned, lower_aligned = aligned

    out = ta_py.in_channel(
        [float(v) for v in price_aligned.values],
        [float(v) for v in upper_aligned.values],
        [float(v) for v in lower_aligned.values],
    )
    return _bool_values_to_series(out, price_aligned)


OUT_SPEC = IndicatorSpec(
    name="out",
    description="Detect when price is outside channel (above upper or below lower)",
    inputs=(InputSlotSpec(name="price", required=False, default_source="ohlcv", default_field="close"),),
    params={
        "price": ParamSpec(name="price", type=object, default=None, required=False),
        "upper": ParamSpec(name="upper", type=object, default=None, required=False),
        "lower": ParamSpec(name="lower", type=object, default=None, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Price outside channel", role="line")},
    semantics=SemanticsSpec(required_fields=("close",), input_field="close", input_series_param="price"),
    runtime_binding=RuntimeBindingSpec(kernel_id="out"),
)


@register(spec=OUT_SPEC)
def out(
    ctx: SeriesContext,
    price: Series[Price] | Any | None = None,
    upper: Series[Price] | Any | float | int | Decimal | None = None,
    lower: Series[Price] | Any | float | int | Decimal | None = None,
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
    channel_bounds = resolve_channel_tuple(price, ctx) if upper is None and lower is None else None

    if channel_bounds is not None:
        upper_series, lower_series = channel_bounds
        price_series = resolve_series_input(None, ctx, reference_series=upper_series)
    else:
        price_series = resolve_series_input(price, ctx)
        upper_series = resolve_series_input(upper, ctx, reference_series=price_series)
        lower_series = resolve_series_input(lower, ctx, reference_series=price_series)

    if len(price_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=price_series.symbol, timeframe=price_series.timeframe)

    aligned = _align_price_upper_lower(price_series, upper_series, lower_series)
    if aligned is None:
        return Series[bool](timestamps=(), values=(), symbol=price_series.symbol, timeframe=price_series.timeframe)
    price_aligned, upper_aligned, lower_aligned = aligned

    out_vals = ta_py.out_channel(
        [float(v) for v in price_aligned.values],
        [float(v) for v in upper_aligned.values],
        [float(v) for v in lower_aligned.values],
    )
    return _bool_values_to_series(out_vals, price_aligned)


ENTER_SPEC = IndicatorSpec(
    name="enter",
    description="Detect when price enters channel (was outside, now inside)",
    inputs=(InputSlotSpec(name="price", required=False, default_source="ohlcv", default_field="close"),),
    params={
        "price": ParamSpec(name="price", type=object, default=None, required=False),
        "upper": ParamSpec(name="upper", type=object, default=None, required=False),
        "lower": ParamSpec(name="lower", type=object, default=None, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Price enters channel", role="line")},
    semantics=SemanticsSpec(required_fields=("close",), input_field="close", input_series_param="price"),
    runtime_binding=RuntimeBindingSpec(kernel_id="enter"),
)


@register(spec=ENTER_SPEC)
def enter(
    ctx: SeriesContext,
    price: Series[Price] | Any | None = None,
    upper: Series[Price] | Any | float | int | Decimal | None = None,
    lower: Series[Price] | Any | float | int | Decimal | None = None,
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
    channel_bounds = resolve_channel_tuple(price, ctx) if upper is None and lower is None else None

    if channel_bounds is not None:
        upper_series, lower_series = channel_bounds
        price_series = resolve_series_input(None, ctx, reference_series=upper_series)
    else:
        price_series = resolve_series_input(price, ctx)
        upper_series = resolve_series_input(upper, ctx, reference_series=price_series)
        lower_series = resolve_series_input(lower, ctx, reference_series=price_series)

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

    out_vals = ta_py.enter_channel(
        [float(v) for v in price_aligned.values],
        [float(v) for v in upper_aligned.values],
        [float(v) for v in lower_aligned.values],
    )
    return _bool_values_to_series(out_vals, price_aligned)


EXIT_SPEC = IndicatorSpec(
    name="exit",
    description="Detect when price exits channel (was inside, now outside)",
    inputs=(InputSlotSpec(name="price", required=False, default_source="ohlcv", default_field="close"),),
    params={
        "price": ParamSpec(name="price", type=object, default=None, required=False),
        "upper": ParamSpec(name="upper", type=object, default=None, required=False),
        "lower": ParamSpec(name="lower", type=object, default=None, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Price exits channel", role="line")},
    semantics=SemanticsSpec(required_fields=("close",), input_field="close", input_series_param="price"),
    runtime_binding=RuntimeBindingSpec(kernel_id="exit"),
)


@register(spec=EXIT_SPEC)
def exit(
    ctx: SeriesContext,
    price: Series[Price] | Any | None = None,
    upper: Series[Price] | Any | float | int | Decimal | None = None,
    lower: Series[Price] | Any | float | int | Decimal | None = None,
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
    channel_bounds = resolve_channel_tuple(price, ctx) if upper is None and lower is None else None

    if channel_bounds is not None:
        upper_series, lower_series = channel_bounds
        price_series = resolve_series_input(None, ctx, reference_series=upper_series)
    else:
        price_series = resolve_series_input(price, ctx)
        upper_series = resolve_series_input(upper, ctx, reference_series=price_series)
        lower_series = resolve_series_input(lower, ctx, reference_series=price_series)

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

    out_vals = ta_py.exit_channel(
        [float(v) for v in price_aligned.values],
        [float(v) for v in upper_aligned.values],
        [float(v) for v in lower_aligned.values],
    )
    return _bool_values_to_series(out_vals, price_aligned)
