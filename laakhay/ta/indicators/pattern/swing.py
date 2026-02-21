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

    hi_vals = tuple(Decimal(v) for v in high.values)
    lo_vals = tuple(Decimal(v) for v in low.values)

    raw_high = [False] * n
    raw_low = [False] * n
    flags_high = [False] * n  # confirmed/visible swings (no-lookahead)
    flags_low = [False] * n  # confirmed/visible swings (no-lookahead)
    have_confirmed_high = False

    window = left + right
    mask_eval = [idx >= window for idx in range(n)]
    if n <= window:
        # Not enough observations to confirm any swing
        empty_pivots = tuple()
        return _SwingSeries(tuple(flags_high), tuple(flags_low), tuple(mask_eval), empty_pivots, empty_pivots)

    for idx in range(left, n - right):
        window_start = idx - left
        window_end = idx + right + 1  # inclusive of idx + right

        hi_window = hi_vals[window_start:window_end]
        lo_window = lo_vals[window_start:window_end]

        cur_high = hi_vals[idx]
        cur_low = lo_vals[idx]

        high_is_extreme = cur_high == max(hi_window)
        high_is_unique = hi_window.count(cur_high) == 1
        if high_is_extreme and (allow_equal_extremes or high_is_unique):
            raw_high[idx] = True
            have_confirmed_high = True

        low_is_extreme = cur_low == min(lo_window)
        low_is_unique = lo_window.count(cur_low) == 1
        if have_confirmed_high and low_is_extreme and (allow_equal_extremes or low_is_unique):
            raw_low[idx] = True

    confirmed_high: list[_ConfirmedPivot] = []
    confirmed_low: list[_ConfirmedPivot] = []
    for pivot_idx in range(n):
        confirmed_idx = pivot_idx + right
        if confirmed_idx >= n:
            continue
        if raw_high[pivot_idx]:
            flags_high[confirmed_idx] = True
            confirmed_high.append(
                _ConfirmedPivot(pivot_idx=pivot_idx, confirmed_idx=confirmed_idx, price=hi_vals[pivot_idx])
            )
        if raw_low[pivot_idx]:
            flags_low[confirmed_idx] = True
            confirmed_low.append(
                _ConfirmedPivot(pivot_idx=pivot_idx, confirmed_idx=confirmed_idx, price=lo_vals[pivot_idx])
            )

    return _SwingSeries(
        tuple(flags_high),
        tuple(flags_low),
        tuple(mask_eval),
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


@register(
    "swing_points",
    description="Detect swing highs and lows using fractal-style lookbacks",
    output_metadata={
        "swing_high": {"type": "price", "role": "level", "polarity": "high"},
        "swing_low": {"type": "price", "role": "level", "polarity": "low"},
    },
)
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


@register(
    "swing_highs",
    description="Detect swing highs using fractal-style lookbacks",
    output_metadata={"result": {"type": "price", "role": "level", "polarity": "high"}},
)
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


@register(
    "swing_lows",
    description="Detect swing lows using fractal-style lookbacks",
    output_metadata={"result": {"type": "price", "role": "level", "polarity": "low"}},
)
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


@register(
    "swing_high_at",
    description="Price series for the nth latest confirmed swing high",
    output_metadata={"result": {"type": "price", "role": "level", "polarity": "high"}},
)
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


@register(
    "swing_low_at",
    description="Price series for the nth latest confirmed swing low",
    output_metadata={"result": {"type": "price", "role": "level", "polarity": "low"}},
)
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
