"""Fibonacci retracement utilities built on swing structure."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Dict, Literal

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...registry.models import SeriesContext
from ...registry.registry import register
from .swing import _compute_swings, _validate_inputs


def _as_decimal(level: float | Decimal) -> Decimal:
    if isinstance(level, Decimal):
        return level
    return Decimal(str(level))


def _make_price_series(base: Series[Price], values: Iterable[Decimal | Price], mask: Iterable[bool]) -> Series[Price]:
    return CoreSeries[Price](
        timestamps=base.timestamps,
        values=tuple(Decimal(v) for v in values),
        symbol=base.symbol,
        timeframe=base.timeframe,
        availability_mask=tuple(mask),
    )


@register(
    "fib_retracement",
    description="Compute Fibonacci retracement bands from recent swing structure",
    output_metadata={
        "anchor_high": {"type": "price", "role": "anchor_high"},
        "anchor_low": {"type": "price", "role": "anchor_low"},
        "down": {"type": "dict", "role": "levels_down"},
        "up": {"type": "dict", "role": "levels_up"},
    },
)
def fib_retracement(
    ctx: SeriesContext,
    *,
    left: int = 2,
    right: int = 2,
    levels: tuple[float | Decimal, ...] = (0.382, 0.5, 0.618),
    mode: Literal["both", "down", "up"] = "both",
) -> Dict[str, Series[Price] | Dict[str, Series[Price]]]:
    """
    Derive Fibonacci retracement levels from the latest confirmed swing highs and lows.

    Args:
        ctx: Series context containing `high` and `low` price series.
        left: Swing lookback window to the left (see `swing_points`).
        right: Swing lookback window to the right (see `swing_points`).
        levels: Fibonacci ratios to project between swing anchors.
        mode: Which retracement directions to return: downward (from high), upward (from low), or both.

    Returns:
        Dictionary with anchor series and per-direction level series dictionaries.
    """
    high, low = _validate_inputs(ctx, left, right)

    swings = _compute_swings(high, low, left, right)
    hi_vals = tuple(Decimal(v) for v in high.values)
    lo_vals = tuple(Decimal(v) for v in low.values)

    n = len(high)
    if n == 0:
        empty = _make_price_series(high, (), ())
        return {
            "anchor_high": empty,
            "anchor_low": empty,
            "down": {},
            "up": {},
        }

    anchor_high_vals: list[Decimal] = []
    anchor_low_vals: list[Decimal] = []
    anchor_high_mask: list[bool] = []
    anchor_low_mask: list[bool] = []

    current_high: Decimal | None = None
    current_low: Decimal | None = None
    current_high_idx = -1
    current_low_idx = -1

    for idx in range(n):
        if swings.flags_high[idx]:
            current_high = hi_vals[idx]
            current_high_idx = idx
        elif current_high is None or hi_vals[idx] > current_high:
            current_high = hi_vals[idx]
            current_high_idx = idx

        if swings.flags_low[idx]:
            current_low = lo_vals[idx]
            current_low_idx = idx
        elif current_low is None or lo_vals[idx] < current_low:
            current_low = lo_vals[idx]
            current_low_idx = idx

        anchor_high_vals.append(current_high if current_high is not None else hi_vals[idx])
        anchor_low_vals.append(current_low if current_low is not None else lo_vals[idx])

        prev_high_mask = anchor_high_mask[-1] if anchor_high_mask else False
        prev_low_mask = anchor_low_mask[-1] if anchor_low_mask else False
        anchor_high_confirmed = swings.flags_high[idx] or (
            current_high is not None and current_high_idx >= 0 and swings.mask_eval[idx]
        )
        anchor_low_confirmed = swings.flags_low[idx] or (
            current_low is not None and current_low_idx >= 0 and swings.mask_eval[idx]
        )
        anchor_high_mask.append(prev_high_mask or anchor_high_confirmed)
        anchor_low_mask.append(prev_low_mask or anchor_low_confirmed)
    # Prepare level containers
    level_decimals = tuple(_as_decimal(lvl) for lvl in levels)
    down_values = {str(lvl): [] for lvl in level_decimals}
    down_mask = {str(lvl): [] for lvl in level_decimals}
    up_values = {str(lvl): [] for lvl in level_decimals}
    up_mask = {str(lvl): [] for lvl in level_decimals}

    for idx in range(n):
        if swings.flags_high[idx]:
            current_high = hi_vals[idx]
            current_high_idx = idx
        if swings.flags_low[idx]:
            current_low = lo_vals[idx]
            current_low_idx = idx

        has_high = current_high is not None
        has_low = current_low is not None

        if has_high and has_low:
            assert current_high is not None and current_low is not None
            price_range = current_high - current_low
            # Guard zero or negative ranges
            valid_range = price_range.copy_abs() > 0

            for lvl in level_decimals:
                lvl_key = str(lvl)

                down_ready = anchor_high_mask[idx] and anchor_low_mask[idx]
                up_ready = anchor_high_mask[idx] and anchor_low_mask[idx]

                # Downward retracement: recent move up (high after low)
                can_down = valid_range and current_high_idx >= current_low_idx >= 0 and current_high > current_low
                if can_down and down_ready:
                    down_price = current_high - (current_high - current_low) * lvl
                    down_values[lvl_key].append(down_price)
                    down_mask[lvl_key].append(True)
                else:
                    down_values[lvl_key].append(current_high if has_high else hi_vals[idx])
                    down_mask[lvl_key].append(False)

                # Upward retracement: recent move down (low after high)
                can_up = valid_range and current_low_idx >= current_high_idx >= 0 and current_high > current_low
                if can_up and up_ready:
                    up_price = current_low + (current_high - current_low) * lvl
                    up_values[lvl_key].append(up_price)
                    up_mask[lvl_key].append(True)
                else:
                    up_values[lvl_key].append(current_low if has_low else lo_vals[idx])
                    up_mask[lvl_key].append(False)
        else:
            for lvl in level_decimals:
                lvl_key = str(lvl)
                down_values[lvl_key].append(hi_vals[idx])
                down_mask[lvl_key].append(False)
                up_values[lvl_key].append(lo_vals[idx])
                up_mask[lvl_key].append(False)

    anchor_high_series = _make_price_series(high, anchor_high_vals, anchor_high_mask)
    anchor_low_series = _make_price_series(low, anchor_low_vals, anchor_low_mask)

    result: dict[str, Series[Price] | dict[str, Series[Price]]] = {
        "anchor_high": anchor_high_series,
        "anchor_low": anchor_low_series,
        "down": {},
        "up": {},
    }

    if mode in ("both", "down"):
        for lvl in level_decimals:
            key = str(lvl)
            result["down"][key] = _make_price_series(high, down_values[key], down_mask[key])
    if mode in ("both", "up"):
        for lvl in level_decimals:
            key = str(lvl)
            result["up"][key] = _make_price_series(low, up_values[key], up_mask[key])

    return result


__all__ = ["fib_retracement"]
