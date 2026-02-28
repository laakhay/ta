"""Swing structure detection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Literal

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)


def _validate_inputs(ctx: SeriesContext, left: int, right: int) -> tuple[Series[Price], Series[Price]]:
    if left < 1 or right < 1:
        raise ValueError("left and right must be positive integers")
    if not hasattr(ctx, "high") or not hasattr(ctx, "low"):
        raise ValueError("swing_points indicator requires 'high' and 'low' series in context")

    high = ctx.high
    low = ctx.low

    if high.symbol != low.symbol or high.timeframe != low.timeframe:
        raise ValueError("high and low series must share symbol and timeframe metadata")
    if len(high) != len(low):
        raise ValueError("high and low series must be the same length")

    return high, low


@dataclass(frozen=True)
class _SwingSeries:
    flags_high: tuple[bool, ...]
    flags_low: tuple[bool, ...]
    mask_eval: tuple[bool, ...]
    confirmed_high: tuple[_ConfirmedPivot, ...]
    confirmed_low: tuple[_ConfirmedPivot, ...]


@dataclass(frozen=True)
class _ConfirmedPivot:
    pivot_idx: int
    confirmed_idx: int
    price: Decimal


import ta_py

def _compute_swings(
    high: Series[Price],
    low: Series[Price],
    left: int,
    right: int,
    *,
    allow_equal_extremes: bool = False,
) -> _SwingSeries:
    n = len(high)
    if n == 0:
        empty_flags: tuple[bool, ...] = tuple()
        empty_pivots: tuple[_ConfirmedPivot, ...] = tuple()
        return _SwingSeries(empty_flags, empty_flags, empty_flags, empty_pivots, empty_pivots)

    hi_vals = [float(v) for v in high.values]
    lo_vals = [float(v) for v in low.values]

    # Call Rust kernel
    res_high, res_low = ta_py.swing_points_raw(
        hi_vals, lo_vals, left, right, allow_equal_extremes
    )

    confirmed_high = []
    confirmed_low = []
    
    for i in range(n):
        pivot_idx = i - right
        if pivot_idx < 0:
            continue
        if res_high[i]:
            confirmed_high.append(_ConfirmedPivot(
                pivot_idx=pivot_idx, confirmed_idx=i, price=Decimal(str(hi_vals[pivot_idx]))
            ))
        if res_low[i]:
            confirmed_low.append(_ConfirmedPivot(
                pivot_idx=pivot_idx, confirmed_idx=i, price=Decimal(str(lo_vals[pivot_idx]))
            ))

    mask_eval = tuple(idx >= (left + right) for idx in range(n))

    return _SwingSeries(
        tuple(res_high),
        tuple(res_low),
        mask_eval,
        tuple(confirmed_high),
        tuple(confirmed_low),
    )


def _make_flag_series(
    base: Series[Price],
    flags: tuple[bool, ...],
    availability: tuple[bool, ...],
    *,
    events: tuple[_ConfirmedPivot, ...],
    inherit_prices: bool = False,
) -> Series[Price] | Series[bool]:
    if inherit_prices:
        values = list(base.values)
        mask = [False] * len(values)
        for event in events:
            values[event.confirmed_idx] = event.price
            mask[event.confirmed_idx] = True
        return CoreSeries[Price](
            timestamps=base.timestamps,
            values=tuple(values),  # type: ignore[arg-type]
            symbol=base.symbol,
            timeframe=base.timeframe,
            availability_mask=tuple(mask),
        )

    return Series[bool](
        timestamps=base.timestamps,
        values=flags,
        symbol=base.symbol,
        timeframe=base.timeframe,
        availability_mask=availability,
    )


def _build_result(
    ctx: SeriesContext,
    left: int,
    right: int,
    *,
    return_mode: Literal["flags", "levels"],
    subset: Literal["both", "high", "low"],
    allow_equal_extremes: bool = False,
) -> Dict[str, Series]:
    high, low = _validate_inputs(ctx, left, right)
    result = _compute_swings(high, low, left, right, allow_equal_extremes=allow_equal_extremes)

    if return_mode not in {"flags", "levels"}:
        raise ValueError("return_mode must be 'flags' or 'levels'")

    inherit_prices = return_mode == "levels"

    swing_high = _make_flag_series(
        high,
        result.flags_high,
        result.mask_eval,
        events=result.confirmed_high,
        inherit_prices=inherit_prices,
    )
    swing_low = _make_flag_series(
        low,
        result.flags_low,
        result.mask_eval,
        events=result.confirmed_low,
        inherit_prices=inherit_prices,
    )

    output: Dict[str, Series] = {}
    if subset in {"both", "high"}:
        output["swing_high"] = swing_high
    if subset in {"both", "low"}:
        output["swing_low"] = swing_low
    return output


SWING_POINTS_SPEC = IndicatorSpec(
    name="swing_points",
    description="Detect swing highs and lows using fractal-style lookbacks",
    params={
        "left": ParamSpec(name="left", type=int, default=2, required=False),
        "right": ParamSpec(name="right", type=int, default=2, required=False),
        "return_mode": ParamSpec(name="return_mode", type=str, default="flags", required=False),
        "allow_equal_extremes": ParamSpec(name="allow_equal_extremes", type=bool, default=False, required=False),
    },
    outputs={
        "swing_high": OutputSpec(
            name="swing_high", type=Series, description="Swing high flags/levels", role="level", polarity="high"
        ),
        "swing_low": OutputSpec(
            name="swing_low", type=Series, description="Swing low flags/levels", role="level", polarity="low"
        ),
    },
    semantics=SemanticsSpec(required_fields=("high", "low"), lookback_params=("left", "right")),
    runtime_binding=RuntimeBindingSpec(kernel_id="swing_points"),
)


@register(spec=SWING_POINTS_SPEC)
def swing_points(
    ctx: SeriesContext,
    *,
    left: int = 2,
    right: int = 2,
    return_mode: Literal["flags", "levels"] = "flags",
    allow_equal_extremes: bool = False,
) -> Dict[str, Series]:
    """
    Identify swing highs and lows using configurable lookback widths.

    Args:
        ctx: Series context containing `high` and `low` price series.
        left: Number of bars to the left that must be lower (for highs) or higher (for lows).
        right: Number of bars to the right that must be lower or higher.
        return_mode: Either "flags" (booleans) or "levels" (price series with availability mask).

    Returns:
        Dictionary containing `swing_high` and `swing_low` series.
    """
    return _build_result(
        ctx,
        left,
        right,
        return_mode=return_mode,
        subset="both",
        allow_equal_extremes=allow_equal_extremes,
    )


SWING_HIGHS_SPEC = IndicatorSpec(
    name="swing_highs",
    description="Detect swing highs using fractal-style lookbacks",
    params={
        "left": ParamSpec(name="left", type=int, default=2, required=False),
        "right": ParamSpec(name="right", type=int, default=2, required=False),
        "return_mode": ParamSpec(name="return_mode", type=str, default="flags", required=False),
        "allow_equal_extremes": ParamSpec(name="allow_equal_extremes", type=bool, default=False, required=False),
    },
    outputs={
        "result": OutputSpec(
            name="result", type=Series, description="Swing high flags/levels", role="level", polarity="high"
        )
    },
    semantics=SemanticsSpec(required_fields=("high", "low"), lookback_params=("left", "right")),
    runtime_binding=RuntimeBindingSpec(kernel_id="swing_highs"),
)


@register(spec=SWING_HIGHS_SPEC)
def swing_highs(
    ctx: SeriesContext,
    *,
    left: int = 2,
    right: int = 2,
    return_mode: Literal["flags", "levels"] = "flags",
    allow_equal_extremes: bool = False,
) -> Series[Price] | Series[bool]:
    result = _build_result(
        ctx,
        left,
        right,
        return_mode=return_mode,
        subset="high",
        allow_equal_extremes=allow_equal_extremes,
    )
    return result["swing_high"]


SWING_LOWS_SPEC = IndicatorSpec(
    name="swing_lows",
    description="Detect swing lows using fractal-style lookbacks",
    params={
        "left": ParamSpec(name="left", type=int, default=2, required=False),
        "right": ParamSpec(name="right", type=int, default=2, required=False),
        "return_mode": ParamSpec(name="return_mode", type=str, default="flags", required=False),
        "allow_equal_extremes": ParamSpec(name="allow_equal_extremes", type=bool, default=False, required=False),
    },
    outputs={
        "result": OutputSpec(
            name="result", type=Series, description="Swing low flags/levels", role="level", polarity="low"
        )
    },
    semantics=SemanticsSpec(required_fields=("high", "low"), lookback_params=("left", "right")),
    runtime_binding=RuntimeBindingSpec(kernel_id="swing_lows"),
)


@register(spec=SWING_LOWS_SPEC)
def swing_lows(
    ctx: SeriesContext,
    *,
    left: int = 2,
    right: int = 2,
    return_mode: Literal["flags", "levels"] = "flags",
    allow_equal_extremes: bool = False,
) -> Series[Price] | Series[bool]:
    result = _build_result(
        ctx,
        left,
        right,
        return_mode=return_mode,
        subset="low",
        allow_equal_extremes=allow_equal_extremes,
    )
    return result["swing_low"]


def _build_indexed_level_series(
    base: Series[Price],
    confirmed_events: tuple[_ConfirmedPivot, ...],
    *,
    index: int,
) -> Series[Price]:
    if index < 1:
        raise ValueError("index must be a positive integer")

    selected_values: list[Decimal] = []
    selected_mask: list[bool] = []
    confirmed_levels: list[Decimal] = []
    base_values = tuple(Decimal(v) for v in base.values)
    events_by_confirm_idx: dict[int, list[_ConfirmedPivot]] = {}
    for event in confirmed_events:
        events_by_confirm_idx.setdefault(event.confirmed_idx, []).append(event)

    for idx in range(len(base_values)):
        for event in events_by_confirm_idx.get(idx, []):
            confirmed_levels.append(event.price)

        if len(confirmed_levels) >= index:
            selected_values.append(confirmed_levels[-index])
            selected_mask.append(True)
        else:
            selected_values.append(base_values[idx])
            selected_mask.append(False)

    return CoreSeries[Price](
        timestamps=base.timestamps,
        values=tuple(selected_values),
        symbol=base.symbol,
        timeframe=base.timeframe,
        availability_mask=tuple(selected_mask),
    )


SWING_HIGH_AT_SPEC = IndicatorSpec(
    name="swing_high_at",
    description="Price series for the nth latest confirmed swing high",
    params={
        "index": ParamSpec(name="index", type=int, default=1, required=False),
        "left": ParamSpec(name="left", type=int, default=2, required=False),
        "right": ParamSpec(name="right", type=int, default=2, required=False),
        "allow_equal_extremes": ParamSpec(name="allow_equal_extremes", type=bool, default=False, required=False),
    },
    outputs={
        "result": OutputSpec(
            name="result", type=Series, description="Nth swing high price", role="level", polarity="high"
        )
    },
    semantics=SemanticsSpec(required_fields=("high", "low"), lookback_params=("left", "right", "index")),
    runtime_binding=RuntimeBindingSpec(kernel_id="swing_high_at"),
)


@register(spec=SWING_HIGH_AT_SPEC)
def swing_high_at(
    ctx: SeriesContext,
    *,
    index: int = 1,
    left: int = 2,
    right: int = 2,
    allow_equal_extremes: bool = False,
) -> Series[Price]:
    high, low = _validate_inputs(ctx, left, right)
    swings = _compute_swings(high, low, left, right, allow_equal_extremes=allow_equal_extremes)
    return _build_indexed_level_series(high, swings.confirmed_high, index=index)


SWING_LOW_AT_SPEC = IndicatorSpec(
    name="swing_low_at",
    description="Price series for the nth latest confirmed swing low",
    params={
        "index": ParamSpec(name="index", type=int, default=1, required=False),
        "left": ParamSpec(name="left", type=int, default=2, required=False),
        "right": ParamSpec(name="right", type=int, default=2, required=False),
        "allow_equal_extremes": ParamSpec(name="allow_equal_extremes", type=bool, default=False, required=False),
    },
    outputs={
        "result": OutputSpec(
            name="result", type=Series, description="Nth swing low price", role="level", polarity="low"
        )
    },
    semantics=SemanticsSpec(required_fields=("high", "low"), lookback_params=("left", "right", "index")),
    runtime_binding=RuntimeBindingSpec(kernel_id="swing_low_at"),
)


@register(spec=SWING_LOW_AT_SPEC)
def swing_low_at(
    ctx: SeriesContext,
    *,
    index: int = 1,
    left: int = 2,
    right: int = 2,
    allow_equal_extremes: bool = False,
) -> Series[Price]:
    high, low = _validate_inputs(ctx, left, right)
    swings = _compute_swings(high, low, left, right, allow_equal_extremes=allow_equal_extremes)
    return _build_indexed_level_series(low, swings.confirmed_low, index=index)


__all__ = ["swing_points", "swing_highs", "swing_lows", "swing_high_at", "swing_low_at"]
