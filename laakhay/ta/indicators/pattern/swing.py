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


def _compute_swings(high: Series[Price], low: Series[Price], left: int, right: int) -> _SwingSeries:
    n = len(high)
    if n == 0:
        empty_flags: tuple[bool, ...] = tuple()
        return _SwingSeries(empty_flags, empty_flags, empty_flags)

    hi_vals = tuple(Decimal(v) for v in high.values)
    lo_vals = tuple(Decimal(v) for v in low.values)

    flags_high = [False] * n
    flags_low = [False] * n
    mask_eval = [False] * n
    have_confirmed_high = False

    window = left + right
    if n <= window:
        # Not enough observations to confirm any swing
        return _SwingSeries(tuple(flags_high), tuple(flags_low), tuple(mask_eval))

    for idx in range(left, n - right):
        mask_eval[idx] = True

        window_start = idx - left
        window_end = idx + right + 1  # inclusive of idx + right

        hi_window = hi_vals[window_start:window_end]
        lo_window = lo_vals[window_start:window_end]

        cur_high = hi_vals[idx]
        cur_low = lo_vals[idx]

        if cur_high == max(hi_window) and hi_window.count(cur_high) == 1:
            flags_high[idx] = True
            have_confirmed_high = True

        if have_confirmed_high and cur_low == min(lo_window) and lo_window.count(cur_low) == 1:
            flags_low[idx] = True

    return _SwingSeries(tuple(flags_high), tuple(flags_low), tuple(mask_eval))


def _make_flag_series(
    base: Series[Price],
    flags: tuple[bool, ...],
    availability: tuple[bool, ...],
    *,
    inherit_prices: bool = False,
) -> Series[Price] | Series[bool]:
    if inherit_prices:
        values = base.values
        mask = tuple(flag and avail for flag, avail in zip(flags, availability, strict=False))
        return CoreSeries[Price](
            timestamps=base.timestamps,
            values=values,  # type: ignore[arg-type]
            symbol=base.symbol,
            timeframe=base.timeframe,
            availability_mask=mask,
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
) -> Dict[str, Series]:
    high, low = _validate_inputs(ctx, left, right)
    result = _compute_swings(high, low, left, right)

    if return_mode not in {"flags", "levels"}:
        raise ValueError("return_mode must be 'flags' or 'levels'")

    inherit_prices = return_mode == "levels"

    swing_high = _make_flag_series(high, result.flags_high, result.mask_eval, inherit_prices=inherit_prices)
    swing_low = _make_flag_series(low, result.flags_low, result.mask_eval, inherit_prices=inherit_prices)

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
    return _build_result(ctx, left, right, return_mode=return_mode, subset="both")


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
) -> Series[Price] | Series[bool]:
    result = _build_result(ctx, left, right, return_mode=return_mode, subset="high")
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
) -> Series[Price] | Series[bool]:
    result = _build_result(ctx, left, right, return_mode=return_mode, subset="low")
    return result["swing_low"]


__all__ = ["swing_points", "swing_highs", "swing_lows"]
