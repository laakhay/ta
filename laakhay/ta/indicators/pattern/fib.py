"""Fibonacci retracement utilities built on swing structure."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
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
from .swing import _compute_swings, _ConfirmedPivot, _validate_inputs

_PAIRING_MODES = ("strict_alternating", "latest_valid")


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


@dataclass(frozen=True)
class _Pivot:
    idx: int
    kind: Literal["high", "low"]
    price: Decimal


@dataclass(frozen=True)
class _Leg:
    low_idx: int
    high_idx: int
    low_price: Decimal
    high_price: Decimal
    end_idx: int


def _validate_fib_params(
    *,
    leg: int,
    pairing_mode: str,
    max_leg_age_bars: int | None,
    min_leg_size_pct: Decimal | None,
) -> None:
    if leg < 1:
        raise ValueError("leg must be a positive integer")
    if pairing_mode not in _PAIRING_MODES:
        raise ValueError(f"pairing_mode must be one of {_PAIRING_MODES}")
    if max_leg_age_bars is not None and max_leg_age_bars < 0:
        raise ValueError("max_leg_age_bars must be >= 0 when provided")
    if min_leg_size_pct is not None and min_leg_size_pct < 0:
        raise ValueError("min_leg_size_pct must be >= 0 when provided")


def _collect_pivots(
    swings_high: tuple[_ConfirmedPivot, ...],
    swings_low: tuple[_ConfirmedPivot, ...],
) -> list[_Pivot]:
    pivots: list[_Pivot] = []
    for pivot in swings_high:
        pivots.append(_Pivot(idx=pivot.confirmed_idx, kind="high", price=pivot.price))
    for pivot in swings_low:
        pivots.append(_Pivot(idx=pivot.confirmed_idx, kind="low", price=pivot.price))
    pivots.sort(key=lambda pivot: (pivot.idx, 0 if pivot.kind == "high" else 1))
    return pivots


def _leg_move_pct(leg: _Leg, direction: Literal["down", "up"]) -> Decimal:
    if direction == "down":
        start = leg.low_price
        end = leg.high_price
    else:
        start = leg.high_price
        end = leg.low_price
    move = (end - start).copy_abs()
    if start == 0:
        return Decimal("Infinity") if move > 0 else Decimal("0")
    return (move / start.copy_abs()) * Decimal("100")


def _keep_leg(
    leg: _Leg,
    direction: Literal["down", "up"],
    min_leg_size_pct: Decimal | None,
) -> bool:
    if leg.high_price <= leg.low_price:
        return False
    if min_leg_size_pct is None:
        return True
    return _leg_move_pct(leg, direction) >= min_leg_size_pct


def _build_legs_strict_alternating(
    pivots: list[_Pivot],
    *,
    direction: Literal["down", "up"],
    min_leg_size_pct: Decimal | None,
) -> list[_Leg]:
    if not pivots:
        return []

    alternating: list[_Pivot] = []
    for pivot in pivots:
        if not alternating:
            alternating.append(pivot)
            continue

        prev = alternating[-1]
        if pivot.kind != prev.kind:
            alternating.append(pivot)
            continue

        if pivot.kind == "high":
            better = pivot.price > prev.price or (pivot.price == prev.price and pivot.idx > prev.idx)
        else:
            better = pivot.price < prev.price or (pivot.price == prev.price and pivot.idx > prev.idx)

        if better:
            alternating[-1] = pivot

    legs: list[_Leg] = []
    for first, second in zip(alternating, alternating[1:], strict=False):
        if direction == "down" and first.kind == "low" and second.kind == "high" and second.idx > first.idx:
            leg = _Leg(
                low_idx=first.idx,
                high_idx=second.idx,
                low_price=first.price,
                high_price=second.price,
                end_idx=second.idx,
            )
            if _keep_leg(leg, direction, min_leg_size_pct):
                legs.append(leg)

        if direction == "up" and first.kind == "high" and second.kind == "low" and second.idx > first.idx:
            leg = _Leg(
                low_idx=second.idx,
                high_idx=first.idx,
                low_price=second.price,
                high_price=first.price,
                end_idx=second.idx,
            )
            if _keep_leg(leg, direction, min_leg_size_pct):
                legs.append(leg)

    return legs


def _build_legs_latest_valid(
    pivots: list[_Pivot],
    *,
    direction: Literal["down", "up"],
    min_leg_size_pct: Decimal | None,
) -> list[_Leg]:
    legs: list[_Leg] = []

    if direction == "down":
        latest_low: _Pivot | None = None
        for pivot in pivots:
            if pivot.kind == "low":
                latest_low = pivot
                continue
            if latest_low is None or pivot.idx <= latest_low.idx:
                continue
            leg = _Leg(
                low_idx=latest_low.idx,
                high_idx=pivot.idx,
                low_price=latest_low.price,
                high_price=pivot.price,
                end_idx=pivot.idx,
            )
            if _keep_leg(leg, direction, min_leg_size_pct):
                legs.append(leg)
    else:
        latest_high: _Pivot | None = None
        for pivot in pivots:
            if pivot.kind == "high":
                latest_high = pivot
                continue
            if latest_high is None or pivot.idx <= latest_high.idx:
                continue
            leg = _Leg(
                low_idx=pivot.idx,
                high_idx=latest_high.idx,
                low_price=pivot.price,
                high_price=latest_high.price,
                end_idx=pivot.idx,
            )
            if _keep_leg(leg, direction, min_leg_size_pct):
                legs.append(leg)

    return legs


def _build_legs(
    pivots: list[_Pivot],
    *,
    direction: Literal["down", "up"],
    pairing_mode: Literal["strict_alternating", "latest_valid"],
    min_leg_size_pct: Decimal | None,
) -> list[_Leg]:
    if pairing_mode == "strict_alternating":
        return _build_legs_strict_alternating(pivots, direction=direction, min_leg_size_pct=min_leg_size_pct)
    return _build_legs_latest_valid(pivots, direction=direction, min_leg_size_pct=min_leg_size_pct)


def _select_legs_timeline(
    *,
    n: int,
    pivots: list[_Pivot],
    leg: int,
    direction: Literal["down", "up"],
    pairing_mode: Literal["strict_alternating", "latest_valid"],
    max_leg_age_bars: int | None,
    min_leg_size_pct: Decimal | None,
    freeze_until_new_leg: bool,
) -> tuple[list[_Leg | None], list[bool]]:
    if n == 0:
        return [], []

    pivots_by_idx: dict[int, list[_Pivot]] = defaultdict(list)
    for pivot in pivots:
        pivots_by_idx[pivot.idx].append(pivot)

    visible_pivots: list[_Pivot] = []
    selected_legs: list[_Leg | None] = []
    valid_mask: list[bool] = []
    current_leg: _Leg | None = None

    for idx in range(n):
        new_pivot = False
        if idx in pivots_by_idx:
            new_pivot = True
            visible_pivots.extend(pivots_by_idx[idx])

        if current_leg is None or not freeze_until_new_leg or new_pivot:
            legs = _build_legs(
                visible_pivots,
                direction=direction,
                pairing_mode=pairing_mode,
                min_leg_size_pct=min_leg_size_pct,
            )
            current_leg = legs[-leg] if len(legs) >= leg else None

        selected_legs.append(current_leg)
        is_valid = current_leg is not None
        if is_valid and max_leg_age_bars is not None:
            assert current_leg is not None
            is_valid = (idx - current_leg.end_idx) <= max_leg_age_bars
        valid_mask.append(is_valid)

    return selected_legs, valid_mask


FIB_RETRACEMENT_SPEC = IndicatorSpec(
    name="fib_retracement",
    description="Compute Fibonacci retracement bands from recent swing structure",
    params={
        "left": ParamSpec(name="left", type=int, default=2, required=False),
        "right": ParamSpec(name="right", type=int, default=2, required=False),
        "levels": ParamSpec(name="levels", type=tuple, default=(0.382, 0.5, 0.618), required=False),
        "mode": ParamSpec(name="mode", type=str, default="both", required=False),
        "leg": ParamSpec(name="leg", type=int, default=1, required=False),
        "pairing_mode": ParamSpec(name="pairing_mode", type=str, default="strict_alternating", required=False),
        "max_leg_age_bars": ParamSpec(name="max_leg_age_bars", type=int, default=None, required=False),
        "min_leg_size_pct": ParamSpec(name="min_leg_size_pct", type=float, default=None, required=False),
        "allow_equal_extremes": ParamSpec(name="allow_equal_extremes", type=bool, default=False, required=False),
        "freeze_until_new_leg": ParamSpec(name="freeze_until_new_leg", type=bool, default=True, required=False),
    },
    outputs={
        "anchor_high": OutputSpec(name="anchor_high", type=Series, description="High anchor", role="anchor_high"),
        "anchor_low": OutputSpec(name="anchor_low", type=Series, description="Low anchor", role="anchor_low"),
        "down": OutputSpec(name="down", type=dict, description="Down retracement levels", role="levels_down"),
        "up": OutputSpec(name="up", type=dict, description="Up retracement levels", role="levels_up"),
    },
    semantics=SemanticsSpec(required_fields=("high", "low"), lookback_params=("left", "right", "leg")),
    runtime_binding=RuntimeBindingSpec(kernel_id="fib_retracement"),
)


@register(spec=FIB_RETRACEMENT_SPEC)
def fib_retracement(
    ctx: SeriesContext,
    *,
    left: int = 2,
    right: int = 2,
    levels: tuple[float | Decimal, ...] = (0.382, 0.5, 0.618),
    mode: Literal["both", "down", "up"] = "both",
    leg: int = 1,
    pairing_mode: Literal["strict_alternating", "latest_valid"] = "strict_alternating",
    max_leg_age_bars: int | None = None,
    min_leg_size_pct: float | Decimal | None = None,
    allow_equal_extremes: bool = False,
    freeze_until_new_leg: bool = True,
) -> Dict[str, Series[Price] | Dict[str, Series[Price]]]:
    """
    Derive Fibonacci retracement levels from confirmed swing legs.

    Args:
        ctx: Series context containing `high` and `low` price series.
        left: Swing lookback window to the left (see `swing_points`).
        right: Swing lookback window to the right (see `swing_points`).
        levels: Fibonacci ratios to project between swing anchors.
        mode: Which retracement directions to return: downward (from high), upward (from low), or both.
        leg: Which confirmed leg to project from (1=latest, 2=previous, ...).
        pairing_mode: Leg-construction policy.
        max_leg_age_bars: Optional max age (bars since leg completion) before invalidating values.
        min_leg_size_pct: Optional minimum leg move percentage.
        allow_equal_extremes: Allow equal highs/lows as swing pivots.
        freeze_until_new_leg: Keep selected leg stable until a new pivot confirms a new leg.

    Returns:
        Dictionary with anchor series and per-direction level series dictionaries.
    """
    min_leg_size = _as_decimal(min_leg_size_pct) if min_leg_size_pct is not None else None
    _validate_fib_params(
        leg=leg,
        pairing_mode=pairing_mode,
        max_leg_age_bars=max_leg_age_bars,
        min_leg_size_pct=min_leg_size,
    )

    high, low = _validate_inputs(ctx, left, right)
    n = len(high)
    if n == 0:
        empty = _make_price_series(high, (), ())
        return {
            "anchor_high": empty,
            "anchor_low": empty,
            "down": {},
            "up": {},
        }

    swings = _compute_swings(high, low, left, right, allow_equal_extremes=allow_equal_extremes)
    hi_vals = tuple(Decimal(v) for v in high.values)
    lo_vals = tuple(Decimal(v) for v in low.values)
    pivots = _collect_pivots(swings.confirmed_high, swings.confirmed_low)

    level_decimals = tuple(_as_decimal(lvl) for lvl in levels)
    for level_decimal in level_decimals:
        if level_decimal < 0 or level_decimal > 2:
            raise ValueError("Fibonacci levels must be between 0 and 2.0")

    down_legs: list[_Leg | None] = [None] * n
    down_valid: list[bool] = [False] * n
    up_legs: list[_Leg | None] = [None] * n
    up_valid: list[bool] = [False] * n

    if mode in {"both", "down"}:
        down_legs, down_valid = _select_legs_timeline(
            n=n,
            pivots=pivots,
            leg=leg,
            direction="down",
            pairing_mode=pairing_mode,
            max_leg_age_bars=max_leg_age_bars,
            min_leg_size_pct=min_leg_size,
            freeze_until_new_leg=freeze_until_new_leg,
        )
    if mode in {"both", "up"}:
        up_legs, up_valid = _select_legs_timeline(
            n=n,
            pivots=pivots,
            leg=leg,
            direction="up",
            pairing_mode=pairing_mode,
            max_leg_age_bars=max_leg_age_bars,
            min_leg_size_pct=min_leg_size,
            freeze_until_new_leg=freeze_until_new_leg,
        )

    anchor_high_values: list[Decimal] = []
    anchor_high_mask: list[bool] = []
    anchor_low_values: list[Decimal] = []
    anchor_low_mask: list[bool] = []

    down_values = {str(level_decimal): [] for level_decimal in level_decimals}
    down_mask = {str(level_decimal): [] for level_decimal in level_decimals}
    up_values = {str(level_decimal): [] for level_decimal in level_decimals}
    up_mask = {str(level_decimal): [] for level_decimal in level_decimals}

    for idx in range(n):
        down_leg = down_legs[idx] if down_valid[idx] else None
        up_leg = up_legs[idx] if up_valid[idx] else None

        chosen_leg: _Leg | None = None
        if mode == "down":
            chosen_leg = down_leg
        elif mode == "up":
            chosen_leg = up_leg
        else:
            if down_leg and up_leg:
                chosen_leg = down_leg if down_leg.end_idx >= up_leg.end_idx else up_leg
            else:
                chosen_leg = down_leg or up_leg

        if chosen_leg is not None:
            anchor_high_values.append(chosen_leg.high_price)
            anchor_high_mask.append(True)
            anchor_low_values.append(chosen_leg.low_price)
            anchor_low_mask.append(True)
        else:
            anchor_high_values.append(hi_vals[idx])
            anchor_high_mask.append(False)
            anchor_low_values.append(lo_vals[idx])
            anchor_low_mask.append(False)

        for level_decimal in level_decimals:
            key = str(level_decimal)
            if down_leg is not None:
                down_price = down_leg.high_price - (down_leg.high_price - down_leg.low_price) * level_decimal
                down_values[key].append(down_price)
                down_mask[key].append(True)
            else:
                down_values[key].append(hi_vals[idx])
                down_mask[key].append(False)

            if up_leg is not None:
                up_price = up_leg.low_price + (up_leg.high_price - up_leg.low_price) * level_decimal
                up_values[key].append(up_price)
                up_mask[key].append(True)
            else:
                up_values[key].append(lo_vals[idx])
                up_mask[key].append(False)

    anchor_high_series = _make_price_series(high, anchor_high_values, anchor_high_mask)
    anchor_low_series = _make_price_series(low, anchor_low_values, anchor_low_mask)

    result: dict[str, Series[Price] | dict[str, Series[Price]]] = {
        "anchor_high": anchor_high_series,
        "anchor_low": anchor_low_series,
        "down": {},
        "up": {},
    }

    if mode in ("both", "down"):
        for level_decimal in level_decimals:
            key = str(level_decimal)
            result["down"][key] = _make_price_series(high, down_values[key], down_mask[key])
    if mode in ("both", "up"):
        for level_decimal in level_decimals:
            key = str(level_decimal)
            result["up"][key] = _make_price_series(low, up_values[key], up_mask[key])

    return result


FIB_ANCHOR_HIGH_SPEC = IndicatorSpec(
    name="fib_anchor_high",
    description="High anchor from the selected confirmed Fibonacci leg",
    aliases=("fib_high_anchor",),
    params={
        "left": ParamSpec(name="left", type=int, default=2, required=False),
        "right": ParamSpec(name="right", type=int, default=2, required=False),
        "leg": ParamSpec(name="leg", type=int, default=1, required=False),
        "pairing_mode": ParamSpec(name="pairing_mode", type=str, default="strict_alternating", required=False),
        "max_leg_age_bars": ParamSpec(name="max_leg_age_bars", type=int, default=None, required=False),
        "min_leg_size_pct": ParamSpec(name="min_leg_size_pct", type=float, default=None, required=False),
        "allow_equal_extremes": ParamSpec(name="allow_equal_extremes", type=bool, default=False, required=False),
        "freeze_until_new_leg": ParamSpec(name="freeze_until_new_leg", type=bool, default=True, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="High anchor", role="anchor_high")},
    semantics=SemanticsSpec(required_fields=("high", "low"), lookback_params=("left", "right", "leg")),
    runtime_binding=RuntimeBindingSpec(kernel_id="fib_anchor_high"),
)


@register(spec=FIB_ANCHOR_HIGH_SPEC)
def fib_anchor_high(
    ctx: SeriesContext,
    *,
    left: int = 2,
    right: int = 2,
    leg: int = 1,
    pairing_mode: Literal["strict_alternating", "latest_valid"] = "strict_alternating",
    max_leg_age_bars: int | None = None,
    min_leg_size_pct: float | Decimal | None = None,
    allow_equal_extremes: bool = False,
    freeze_until_new_leg: bool = True,
) -> Series[Price]:
    result = fib_retracement(
        ctx,
        left=left,
        right=right,
        levels=(),
        mode="both",
        leg=leg,
        pairing_mode=pairing_mode,
        max_leg_age_bars=max_leg_age_bars,
        min_leg_size_pct=min_leg_size_pct,
        allow_equal_extremes=allow_equal_extremes,
        freeze_until_new_leg=freeze_until_new_leg,
    )
    return result["anchor_high"]  # type: ignore[return-value]


FIB_ANCHOR_LOW_SPEC = IndicatorSpec(
    name="fib_anchor_low",
    description="Low anchor from the selected confirmed Fibonacci leg",
    aliases=("fib_low_anchor",),
    params={
        "left": ParamSpec(name="left", type=int, default=2, required=False),
        "right": ParamSpec(name="right", type=int, default=2, required=False),
        "leg": ParamSpec(name="leg", type=int, default=1, required=False),
        "pairing_mode": ParamSpec(name="pairing_mode", type=str, default="strict_alternating", required=False),
        "max_leg_age_bars": ParamSpec(name="max_leg_age_bars", type=int, default=None, required=False),
        "min_leg_size_pct": ParamSpec(name="min_leg_size_pct", type=float, default=None, required=False),
        "allow_equal_extremes": ParamSpec(name="allow_equal_extremes", type=bool, default=False, required=False),
        "freeze_until_new_leg": ParamSpec(name="freeze_until_new_leg", type=bool, default=True, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Low anchor", role="anchor_low")},
    semantics=SemanticsSpec(required_fields=("high", "low"), lookback_params=("left", "right", "leg")),
    runtime_binding=RuntimeBindingSpec(kernel_id="fib_anchor_low"),
)


@register(spec=FIB_ANCHOR_LOW_SPEC)
def fib_anchor_low(
    ctx: SeriesContext,
    *,
    left: int = 2,
    right: int = 2,
    leg: int = 1,
    pairing_mode: Literal["strict_alternating", "latest_valid"] = "strict_alternating",
    max_leg_age_bars: int | None = None,
    min_leg_size_pct: float | Decimal | None = None,
    allow_equal_extremes: bool = False,
    freeze_until_new_leg: bool = True,
) -> Series[Price]:
    result = fib_retracement(
        ctx,
        left=left,
        right=right,
        levels=(),
        mode="both",
        leg=leg,
        pairing_mode=pairing_mode,
        max_leg_age_bars=max_leg_age_bars,
        min_leg_size_pct=min_leg_size_pct,
        allow_equal_extremes=allow_equal_extremes,
        freeze_until_new_leg=freeze_until_new_leg,
    )
    return result["anchor_low"]  # type: ignore[return-value]


FIB_LEVEL_DOWN_SPEC = IndicatorSpec(
    name="fib_level_down",
    description="Single downward Fibonacci retracement level from a selected low->high leg",
    aliases=("fib_down_level", "fib_down"),
    params={
        "level": ParamSpec(name="level", type=float, default=0.618, required=False),
        "left": ParamSpec(name="left", type=int, default=2, required=False),
        "right": ParamSpec(name="right", type=int, default=2, required=False),
        "leg": ParamSpec(name="leg", type=int, default=1, required=False),
        "pairing_mode": ParamSpec(name="pairing_mode", type=str, default="strict_alternating", required=False),
        "max_leg_age_bars": ParamSpec(name="max_leg_age_bars", type=int, default=None, required=False),
        "min_leg_size_pct": ParamSpec(name="min_leg_size_pct", type=float, default=None, required=False),
        "allow_equal_extremes": ParamSpec(name="allow_equal_extremes", type=bool, default=False, required=False),
        "freeze_until_new_leg": ParamSpec(name="freeze_until_new_leg", type=bool, default=True, required=False),
    },
    outputs={
        "result": OutputSpec(name="result", type=Series, description="Down retracement level", role="fib_level_down")
    },
    semantics=SemanticsSpec(required_fields=("high", "low"), lookback_params=("left", "right", "leg")),
    runtime_binding=RuntimeBindingSpec(kernel_id="fib_level_down"),
)


@register(spec=FIB_LEVEL_DOWN_SPEC)
def fib_level_down(
    ctx: SeriesContext,
    *,
    level: float | Decimal = 0.618,
    left: int = 2,
    right: int = 2,
    leg: int = 1,
    pairing_mode: Literal["strict_alternating", "latest_valid"] = "strict_alternating",
    max_leg_age_bars: int | None = None,
    min_leg_size_pct: float | Decimal | None = None,
    allow_equal_extremes: bool = False,
    freeze_until_new_leg: bool = True,
) -> Series[Price]:
    level_decimal = _as_decimal(level)
    result = fib_retracement(
        ctx,
        left=left,
        right=right,
        levels=(level_decimal,),
        mode="down",
        leg=leg,
        pairing_mode=pairing_mode,
        max_leg_age_bars=max_leg_age_bars,
        min_leg_size_pct=min_leg_size_pct,
        allow_equal_extremes=allow_equal_extremes,
        freeze_until_new_leg=freeze_until_new_leg,
    )
    return result["down"][str(level_decimal)]  # type: ignore[index,return-value]


FIB_LEVEL_UP_SPEC = IndicatorSpec(
    name="fib_level_up",
    description="Single upward Fibonacci retracement level from a selected high->low leg",
    aliases=("fib_up_level", "fib_up"),
    params={
        "level": ParamSpec(name="level", type=float, default=0.618, required=False),
        "left": ParamSpec(name="left", type=int, default=2, required=False),
        "right": ParamSpec(name="right", type=int, default=2, required=False),
        "leg": ParamSpec(name="leg", type=int, default=1, required=False),
        "pairing_mode": ParamSpec(name="pairing_mode", type=str, default="strict_alternating", required=False),
        "max_leg_age_bars": ParamSpec(name="max_leg_age_bars", type=int, default=None, required=False),
        "min_leg_size_pct": ParamSpec(name="min_leg_size_pct", type=float, default=None, required=False),
        "allow_equal_extremes": ParamSpec(name="allow_equal_extremes", type=bool, default=False, required=False),
        "freeze_until_new_leg": ParamSpec(name="freeze_until_new_leg", type=bool, default=True, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Up retracement level", role="fib_level_up")},
    semantics=SemanticsSpec(required_fields=("high", "low"), lookback_params=("left", "right", "leg")),
    runtime_binding=RuntimeBindingSpec(kernel_id="fib_level_up"),
)


@register(spec=FIB_LEVEL_UP_SPEC)
def fib_level_up(
    ctx: SeriesContext,
    *,
    level: float | Decimal = 0.618,
    left: int = 2,
    right: int = 2,
    leg: int = 1,
    pairing_mode: Literal["strict_alternating", "latest_valid"] = "strict_alternating",
    max_leg_age_bars: int | None = None,
    min_leg_size_pct: float | Decimal | None = None,
    allow_equal_extremes: bool = False,
    freeze_until_new_leg: bool = True,
) -> Series[Price]:
    level_decimal = _as_decimal(level)
    result = fib_retracement(
        ctx,
        left=left,
        right=right,
        levels=(level_decimal,),
        mode="up",
        leg=leg,
        pairing_mode=pairing_mode,
        max_leg_age_bars=max_leg_age_bars,
        min_leg_size_pct=min_leg_size_pct,
        allow_equal_extremes=allow_equal_extremes,
        freeze_until_new_leg=freeze_until_new_leg,
    )
    return result["up"][str(level_decimal)]  # type: ignore[index,return-value]


__all__ = [
    "fib_retracement",
    "fib_anchor_high",
    "fib_anchor_low",
    "fib_level_down",
    "fib_level_up",
]
