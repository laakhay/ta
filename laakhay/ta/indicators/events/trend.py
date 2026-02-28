"""Trend patterns - Detect rising/falling movements in series."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import ta_py

from ...core import Series
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

RISING_SPEC = IndicatorSpec(
    name="rising",
    description="Detect when series is moving up (current > previous)",
    inputs=(InputSlotSpec(name="a", required=False, default_source="ohlcv", default_field="close"),),
    params={"a": ParamSpec(name="a", type=object, default=None, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="Rising events", role="line")},
    semantics=SemanticsSpec(required_fields=("close",), input_field="close", input_series_param="a"),
    runtime_binding=RuntimeBindingSpec(kernel_id="rising"),
)


@register(spec=RISING_SPEC)
def rising(
    ctx: SeriesContext,
    a: Series[Price] | Any | None = None,
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
    a_series = resolve_series_input(a, ctx)

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

    out = ta_py.rising([float(v) for v in a_series.values])
    return _bool_values_to_series(out, a_series)


FALLING_SPEC = IndicatorSpec(
    name="falling",
    description="Detect when series is moving down (current < previous)",
    inputs=(InputSlotSpec(name="a", required=False, default_source="ohlcv", default_field="close"),),
    params={"a": ParamSpec(name="a", type=object, default=None, required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="Falling events", role="line")},
    semantics=SemanticsSpec(required_fields=("close",), input_field="close", input_series_param="a"),
    runtime_binding=RuntimeBindingSpec(kernel_id="falling"),
)


@register(spec=FALLING_SPEC)
def falling(
    ctx: SeriesContext,
    a: Series[Price] | Any | None = None,
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
    a_series = resolve_series_input(a, ctx)

    if len(a_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)

    if len(a_series) < 2:
        return Series[bool](
            timestamps=a_series.timestamps,
            values=tuple(False for _ in a_series.values),
            symbol=a_series.symbol,
            timeframe=a_series.timeframe,
        )

    out = ta_py.falling([float(v) for v in a_series.values])
    return _bool_values_to_series(out, a_series)


RISING_PCT_SPEC = IndicatorSpec(
    name="rising_pct",
    description="Detect when series has risen by at least pct percent",
    inputs=(InputSlotSpec(name="a", required=False, default_source="ohlcv", default_field="close"),),
    params={
        "a": ParamSpec(name="a", type=object, default=None, required=False),
        "pct": ParamSpec(name="pct", type=float, default=5, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Rising by pct events", role="line")},
    semantics=SemanticsSpec(required_fields=("close",), input_field="close", input_series_param="a"),
    runtime_binding=RuntimeBindingSpec(kernel_id="rising_pct"),
)


@register(spec=RISING_PCT_SPEC)
def rising_pct(
    ctx: SeriesContext,
    a: Series[Price] | Any | None = None,
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
    a_series = resolve_series_input(a, ctx)

    if len(a_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)

    if len(a_series) < 2:
        return Series[bool](
            timestamps=a_series.timestamps,
            values=tuple(False for _ in a_series.values),
            symbol=a_series.symbol,
            timeframe=a_series.timeframe,
        )

    out = ta_py.rising_pct([float(v) for v in a_series.values], float(pct))
    return _bool_values_to_series(out, a_series)


FALLING_PCT_SPEC = IndicatorSpec(
    name="falling_pct",
    description="Detect when series has fallen by at least pct percent",
    inputs=(InputSlotSpec(name="a", required=False, default_source="ohlcv", default_field="close"),),
    params={
        "a": ParamSpec(name="a", type=object, default=None, required=False),
        "pct": ParamSpec(name="pct", type=float, default=5, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Falling by pct events", role="line")},
    semantics=SemanticsSpec(required_fields=("close",), input_field="close", input_series_param="a"),
    runtime_binding=RuntimeBindingSpec(kernel_id="falling_pct"),
)


@register(spec=FALLING_PCT_SPEC)
def falling_pct(
    ctx: SeriesContext,
    a: Series[Price] | Any | None = None,
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
    a_series = resolve_series_input(a, ctx)

    if len(a_series) == 0:
        return Series[bool](timestamps=(), values=(), symbol=a_series.symbol, timeframe=a_series.timeframe)

    if len(a_series) < 2:
        return Series[bool](
            timestamps=a_series.timestamps,
            values=tuple(False for _ in a_series.values),
            symbol=a_series.symbol,
            timeframe=a_series.timeframe,
        )

    out = ta_py.falling_pct([float(v) for v in a_series.values], float(pct))
    return _bool_values_to_series(out, a_series)
