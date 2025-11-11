"""Primitive operations for building indicators using expressions.

This module provides low-level operations that can be composed using
the expression system to create complex indicators.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from decimal import Decimal
from typing import Any, Tuple

from ..core import Series
from ..core.series import Series as CoreSeries
from ..core.types import Price
from ..registry.models import SeriesContext
from ..registry.registry import register

# Import kernel functions with proper type annotations
from ._kernels import (  # type: ignore
    _build_like,  # type: ignore
    _dec,  # type: ignore
    _empty_like,  # type: ignore
    ew_binary,  # type: ignore
    ew_unary,  # type: ignore
    rolling_argmax_deque,  # type: ignore
    rolling_argmin_deque,  # type: ignore
    rolling_kernel,  # type: ignore
    rolling_max_deque,  # type: ignore
    rolling_mean_recipe,  # type: ignore
    rolling_min_deque,  # type: ignore
    rolling_std_recipe,  # type: ignore
    rolling_sum_recipe,  # type: ignore
)

# Type aliases for better linter support
InitFn = Callable[[Iterable[Decimal]], Tuple[Any, Decimal]]
UpdateFn = Callable[[Any, Decimal, Decimal], Tuple[Any, Decimal]]

# Explicit type annotations for kernel functions to help linter
_empty_like: Callable[[Series[Price]], Series[Price]] = _empty_like  # type: ignore
_build_like: Callable[[Series[Price], Iterable[Any], Iterable[Decimal]], Series[Price]] = _build_like  # type: ignore
_dec: Callable[[Any], Decimal] = _dec  # type: ignore
ew_unary: Callable[[Series[Price], Callable[[Decimal], Decimal]], Series[Price]] = ew_unary  # type: ignore
ew_binary: Callable[[Series[Price], Series[Price], Callable[[Decimal, Decimal], Decimal]], Series[Price]] = ew_binary  # type: ignore
rolling_kernel: Callable[..., Series[Price]] = rolling_kernel  # type: ignore
rolling_sum_recipe: Callable[[int], Tuple[InitFn, UpdateFn]] = rolling_sum_recipe  # type: ignore
rolling_mean_recipe: Callable[[int], Tuple[InitFn, UpdateFn]] = rolling_mean_recipe  # type: ignore
rolling_std_recipe: Callable[[int], Tuple[InitFn, UpdateFn]] = rolling_std_recipe  # type: ignore
rolling_max_deque: Callable[[Series[Price], int], Series[Price]] = rolling_max_deque  # type: ignore
rolling_min_deque: Callable[[Series[Price], int], Series[Price]] = rolling_min_deque  # type: ignore
rolling_argmax_deque: Callable[[Series[Price], int], Series[Price]] = rolling_argmax_deque  # type: ignore
rolling_argmin_deque: Callable[[Series[Price], int], Series[Price]] = rolling_argmin_deque  # type: ignore


def _select(ctx: SeriesContext) -> Series[Price]:
    """Pick a reasonable default source series from the context."""
    for c in ("price", "close"):
        if c in ctx.available_series:
            return getattr(ctx, c)
    if not ctx.available_series:
        raise ValueError("SeriesContext has no series to operate on")
    return getattr(ctx, ctx.available_series[0])


def _select_field(ctx: SeriesContext, field: str) -> Series[Price]:
    """Return a specific field from the context, raising if unavailable."""
    # Handle derived price fields
    field_lower = field.lower()

    # hlc3 - Typical Price: (high + low + close) / 3
    if field_lower in ("hlc3", "typical_price"):
        if (
            "high" not in ctx.available_series
            or "low" not in ctx.available_series
            or "close" not in ctx.available_series
        ):
            raise ValueError(f"SeriesContext missing required fields for '{field}': need 'high', 'low', 'close'")
        high = ctx.high
        low = ctx.low
        close = ctx.close
        return (high + low + close) / Decimal(3)

    # ohlc4 - Average Price: (open + high + low + close) / 4
    if field_lower in ("ohlc4", "weighted_close"):
        if (
            "open" not in ctx.available_series
            or "high" not in ctx.available_series
            or "low" not in ctx.available_series
            or "close" not in ctx.available_series
        ):
            raise ValueError(
                f"SeriesContext missing required fields for '{field}': need 'open', 'high', 'low', 'close'"
            )
        open_series = ctx.open
        high = ctx.high
        low = ctx.low
        close = ctx.close
        return (open_series + high + low + close) / Decimal(4)

    # hl2 - Mid Price: (high + low) / 2
    if field_lower in ("hl2", "median_price"):
        if "high" not in ctx.available_series or "low" not in ctx.available_series:
            raise ValueError(f"SeriesContext missing required fields for '{field}': need 'high', 'low'")
        high = ctx.high
        low = ctx.low
        return (high + low) / Decimal(2)

    # range - High - Low
    if field_lower == "range":
        if "high" not in ctx.available_series or "low" not in ctx.available_series:
            raise ValueError(f"SeriesContext missing required fields for '{field}': need 'high', 'low'")
        high = ctx.high
        low = ctx.low
        return high - low

    # upper_wick - High - max(Open, Close)
    if field_lower == "upper_wick":
        if (
            "high" not in ctx.available_series
            or "open" not in ctx.available_series
            or "close" not in ctx.available_series
        ):
            raise ValueError(f"SeriesContext missing required fields for '{field}': need 'high', 'open', 'close'")
        high = ctx.high
        open_series = ctx.open
        close = ctx.close
        # Element-wise max of open and close, then subtract from high
        max_open_close = ew_binary(open_series, close, max)  # type: ignore
        return high - max_open_close

    # lower_wick - min(Open, Close) - Low
    if field_lower == "lower_wick":
        if (
            "open" not in ctx.available_series
            or "close" not in ctx.available_series
            or "low" not in ctx.available_series
        ):
            raise ValueError(f"SeriesContext missing required fields for '{field}': need 'open', 'close', 'low'")
        open_series = ctx.open
        close = ctx.close
        low = ctx.low
        # Element-wise min of open and close, then subtract low
        min_open_close = ew_binary(open_series, close, min)  # type: ignore
        return min_open_close - low

    # Standard fields (close, high, low, open, volume)
    if field in ctx.available_series:
        return getattr(ctx, field)

    raise ValueError(f"SeriesContext missing required field '{field}'")


@register("select", description="Select a named series from the context")
def select(ctx: SeriesContext, field: str = "close") -> Series[Price]:
    """Expose a specific field as an indicator for downstream composition.

    Supports standard fields (close, high, low, open, volume) and derived fields:
    - hlc3 / typical_price: (high + low + close) / 3
    - ohlc4 / weighted_close: (open + high + low + close) / 4
    - hl2 / median_price: (high + low) / 2
    - range: high - low
    - upper_wick: high - max(open, close)
    - lower_wick: min(open, close) - low
    """
    return _select_field(ctx, field)


# ---------- rolling ----------


@register("rolling_sum", description="Rolling sum over a window")
def rolling_sum(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    src = _select(ctx)
    init: InitFn
    upd: UpdateFn
    init, upd = rolling_sum_recipe(period)  # type: ignore
    res = rolling_kernel(src, period, init=init, update=upd)  # type: ignore
    # availability: first period-1 values are not valid
    if len(res) == 0:
        return res
    mask = tuple((i >= period - 1) for i in range(len(res)))
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=mask,
    )


@register("rolling_mean", description="Rolling mean over a window")
def rolling_mean(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    src = _select(ctx)
    init: InitFn
    upd: UpdateFn
    init, upd = rolling_mean_recipe(period)  # type: ignore
    res = rolling_kernel(src, period, init=init, update=upd)  # type: ignore
    if len(res) == 0:
        return res
    mask = tuple((i >= period - 1) for i in range(len(res)))
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=mask,
    )


@register("rolling_std", description="Rolling standard deviation over a window")
def rolling_std(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    src = _select(ctx)
    init: InitFn
    upd: UpdateFn
    init, upd = rolling_std_recipe(period)  # type: ignore
    res = rolling_kernel(src, period, init=init, update=upd)  # type: ignore
    if len(res) == 0:
        return res
    mask = tuple((i >= period - 1) for i in range(len(res)))
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=mask,
    )


@register("max", description="Maximum value in a rolling window")
def rolling_max(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    res = rolling_max_deque(source, period)  # type: ignore
    if len(res) == 0:
        return res
    mask = tuple((i >= period - 1) for i in range(len(res)))
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=mask,
    )


@register("min", description="Minimum value in a rolling window")
def rolling_min(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    res = rolling_min_deque(source, period)  # type: ignore
    if len(res) == 0:
        return res
    mask = tuple((i >= period - 1) for i in range(len(res)))
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=mask,
    )


@register("rolling_argmax", description="Offset of maximum value inside a rolling window")
def rolling_argmax(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    res = rolling_argmax_deque(source, period)  # type: ignore
    if len(res) == 0:
        return res
    mask = tuple((i >= period - 1) for i in range(len(res)))
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=mask,
    )


@register("rolling_argmin", description="Offset of minimum value inside a rolling window")
def rolling_argmin(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    res = rolling_argmin_deque(source, period)  # type: ignore
    if len(res) == 0:
        return res
    mask = tuple((i >= period - 1) for i in range(len(res)))
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=mask,
    )


# Fallback example (rare): rolling_median using generic window_eval
@register("rolling_median", description="Median over window (O(n*w))")
def rolling_median(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    src = _select(ctx)
    return rolling_kernel(src, period, window_eval=lambda w: sorted(w)[len(w) // 2])  # type: ignore


# ---------- element-wise ----------


@register("elementwise_max", description="Element-wise maximum of two series")
def elementwise_max(ctx: SeriesContext, other_series: Series[Price]) -> Series[Price]:
    a = _select(ctx)
    return ew_binary(a, other_series, max)  # type: ignore


@register("elementwise_min", description="Element-wise minimum of two series")
def elementwise_min(ctx: SeriesContext, other_series: Series[Price]) -> Series[Price]:
    a = _select(ctx)
    return ew_binary(a, other_series, min)  # type: ignore


@register("cumulative_sum", description="Cumulative sum of a series")
def cumulative_sum(ctx: SeriesContext) -> Series[Price]:
    src = _select(ctx)
    acc = Decimal(0)
    vals = []
    for v in src.values:
        acc += _dec(v)  # type: ignore
        vals.append(acc)  # type: ignore
    res = _build_like(src, src.timestamps, vals)  # type: ignore
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register("diff", description="Difference between consecutive values")
def diff(ctx: SeriesContext) -> Series[Price]:
    src = _select(ctx)
    if len(src) < 2:
        return _empty_like(src)  # type: ignore
    xs = [_dec(v) for v in src.values]  # type: ignore
    out = [xs[i] - xs[i - 1] for i in range(1, len(xs))]  # type: ignore
    res = _build_like(src, src.timestamps[1:], out)  # type: ignore
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register("shift", description="Shift series by n periods")
def shift(ctx: SeriesContext, periods: int = 1) -> Series[Price]:
    src = _select(ctx)
    n = len(src)
    if n == 0 or periods >= n or periods <= -n:
        return _empty_like(src)  # type: ignore
    if periods == 0:
        return src
    if periods > 0:
        res = Series[Price](
            timestamps=src.timestamps[periods:],
            values=src.values[periods:],
            symbol=src.symbol,
            timeframe=src.timeframe,
        )
        return CoreSeries[Price](
            timestamps=res.timestamps,
            values=res.values,
            symbol=res.symbol,
            timeframe=res.timeframe,
            availability_mask=tuple(True for _ in res.values),
        )
    p = -periods
    res = Series[Price](
        timestamps=src.timestamps[:-p],
        values=src.values[:-p],
        symbol=src.symbol,
        timeframe=src.timeframe,
    )
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register("positive_values", description="Replace negatives with 0")
def positive_values(ctx: SeriesContext) -> Series[Price]:
    return ew_unary(_select(ctx), lambda x: x if x > 0 else Decimal(0))  # type: ignore


@register("negative_values", description="Replace positives with 0")
def negative_values(ctx: SeriesContext) -> Series[Price]:
    return ew_unary(_select(ctx), lambda x: x if x < 0 else Decimal(0))  # type: ignore


@register("rolling_ema", description="Exponential Moving Average over a window")
def rolling_ema(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    src = _select(ctx)
    if period <= 0:
        raise ValueError("Period must be positive")
    if len(src) == 0:
        return _empty_like(src)  # type: ignore
    xs = [_dec(v) for v in src.values]  # type: ignore
    alpha = Decimal(2) / Decimal(period + 1)
    ema = [xs[0]]  # type: ignore
    for i in range(1, len(xs)):  # type: ignore
        ema.append(alpha * xs[i] + (Decimal(1) - alpha) * ema[-1])  # type: ignore
    res = _build_like(src, src.timestamps, ema)  # type: ignore
    # For EMA, mark available from first point by default
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register("true_range", description="True Range for ATR")
def true_range(ctx: SeriesContext) -> Series[Price]:
    for name in ("high", "low", "close"):
        if not hasattr(ctx, name):
            raise ValueError("True Range requires series: ('high','low','close')")
    h, l, c = ctx.high, ctx.low, ctx.close
    if len(c) == 0:
        return _empty_like(c)  # type: ignore
    out = []
    for i in range(len(c)):
        if i == 0:
            tr = _dec(h.values[i]) - _dec(l.values[i])  # type: ignore
        else:
            hl = _dec(h.values[i]) - _dec(l.values[i])  # type: ignore
            hp = abs(_dec(h.values[i]) - _dec(c.values[i - 1]))  # type: ignore
            lp = abs(_dec(l.values[i]) - _dec(c.values[i - 1]))  # type: ignore
            tr = max(hl, hp, lp)  # type: ignore
        out.append(tr)  # type: ignore
    res = _build_like(c, c.timestamps, out)  # type: ignore
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register("typical_price", description="(H+L+C)/3")
def typical_price(ctx: SeriesContext) -> Series[Price]:
    for name in ("high", "low", "close"):
        if not hasattr(ctx, name):
            raise ValueError("Typical Price requires series: ('high','low','close')")
    h, l, c = ctx.high, ctx.low, ctx.close
    if len(c) == 0:
        return _empty_like(c)  # type: ignore
    out = [
        (_dec(hv) + _dec(lv) + _dec(cv)) / Decimal(3) for hv, lv, cv in zip(h.values, l.values, c.values, strict=False)
    ]  # type: ignore
    res = _build_like(c, c.timestamps, out)  # type: ignore
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register("sign", description="Sign of price changes (1, 0, -1)")
def sign(ctx: SeriesContext) -> Series[Price]:
    """Calculate sign of price changes: 1 for positive, -1 for negative, 0 for zero."""
    src = _select(ctx)
    if len(src) < 2:
        return _empty_like(src)  # type: ignore

    xs = [_dec(v) for v in src.values]  # type: ignore
    out = []  # type: ignore
    for i in range(1, len(xs)):  # type: ignore
        diff = xs[i] - xs[i - 1]  # type: ignore
        if diff > 0:
            out.append(Decimal(1))  # type: ignore
        elif diff < 0:
            out.append(Decimal(-1))  # type: ignore
        else:
            out.append(Decimal(0))  # type: ignore

    res = _build_like(src, src.timestamps[1:], out)  # type: ignore
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


# ---------- resample/sync primitives (multi-timeframe helpers) ----------


@register(
    "downsample",
    description="Downsample by factor with aggregation. For OHLCV, uses O/H/L/C/V rules.",
)
def downsample(
    ctx: SeriesContext,
    *,
    factor: int = 2,
    agg: str = "last",
    target: str = "close",
    target_timeframe: str | None = None,
) -> Series[Price] | dict[str, Series[Price]]:
    # If OHLCV present and target=='ohlcv', aggregate each field appropriately
    has_ohlc = all(hasattr(ctx, k) for k in ("open", "high", "low", "close"))
    if target == "ohlcv" and has_ohlc:
        o, h, l, c = ctx.open, ctx.high, ctx.low, ctx.close
        v = getattr(ctx, "volume", None)
        n = len(c)
        if factor <= 1 or n == 0:
            result: dict[str, Series[Price]] = {
                "open": o,
                "high": h,
                "low": l,
                "close": c,
            }
            if v is not None:
                result["volume"] = v
            return result
        result_tf = target_timeframe or c.timeframe
        new_ts = [c.timestamps[min(i + factor - 1, n - 1)] for i in range(0, n, factor)]

        def _bucket(seq):
            return [seq[i : i + factor] for i in range(0, n, factor)]

        ob = _bucket(o.values)
        hb = _bucket(h.values)
        lb = _bucket(l.values)
        cb = _bucket(c.values)
        vb = _bucket(v.values) if v is not None else None
        o_vals = [_dec(b[0]) for b in ob]  # type: ignore
        h_vals = [max(_dec(x) for x in b) for b in hb]  # type: ignore
        l_vals = [min(_dec(x) for x in b) for b in lb]  # type: ignore
        c_vals = [_dec(b[-1]) for b in cb]  # type: ignore
        v_vals = [sum(_dec(x) for x in b) for b in vb] if vb is not None else None  # type: ignore
        o_ser = _build_like(o, new_ts, o_vals)  # type: ignore
        h_ser = _build_like(h, new_ts, h_vals)  # type: ignore
        l_ser = _build_like(l, new_ts, l_vals)  # type: ignore
        c_ser = _build_like(c, new_ts, c_vals)  # type: ignore
        res: dict[str, Series[Price]] = {
            "open": CoreSeries[Price](
                timestamps=o_ser.timestamps,
                values=o_ser.values,
                symbol=o.symbol,
                timeframe=result_tf,
                availability_mask=tuple(True for _ in o_ser.values),
            ),
            "high": CoreSeries[Price](
                timestamps=h_ser.timestamps,
                values=h_ser.values,
                symbol=h.symbol,
                timeframe=result_tf,
                availability_mask=tuple(True for _ in h_ser.values),
            ),
            "low": CoreSeries[Price](
                timestamps=l_ser.timestamps,
                values=l_ser.values,
                symbol=l.symbol,
                timeframe=result_tf,
                availability_mask=tuple(True for _ in l_ser.values),
            ),
            "close": CoreSeries[Price](
                timestamps=c_ser.timestamps,
                values=c_ser.values,
                symbol=c.symbol,
                timeframe=result_tf,
                availability_mask=tuple(True for _ in c_ser.values),
            ),
        }
        if v is not None and v_vals is not None:
            v_ser = _build_like(v, new_ts, v_vals)  # type: ignore
            res["volume"] = CoreSeries[Price](
                timestamps=v_ser.timestamps,
                values=v_ser.values,
                symbol=v.symbol,
                timeframe=result_tf,
                availability_mask=tuple(True for _ in v_ser.values),
            )
        return res

    # Default: operate on selected series (price/close)
    src = _select(ctx)
    if factor <= 1:
        return src
    n = len(src)
    if n == 0:
        return _empty_like(src)  # type: ignore
    buckets = [src.values[i : i + factor] for i in range(0, n, factor)]
    ts_buckets = [src.timestamps[min(i + factor - 1, n - 1)] for i in range(0, n, factor)]
    out_vals: list[Decimal] = []  # type: ignore[type-arg]
    for b in buckets:
        if agg == "last":
            out_vals.append(_dec(b[-1]))  # type: ignore
        elif agg == "mean":
            s = sum(_dec(v) for v in b)  # type: ignore
            out_vals.append(s / Decimal(len(b)))
        elif agg == "sum":
            out_vals.append(sum(_dec(v) for v in b))  # type: ignore
        else:
            raise ValueError("Unsupported agg for downsample: {agg}")
    res = _build_like(src, ts_buckets, out_vals)  # type: ignore
    result_tf = target_timeframe or src.timeframe
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=src.symbol,
        timeframe=result_tf,
        availability_mask=tuple(True for _ in res.values),
    )


@register("upsample", description="Upsample a series by integer factor with forward-fill")
def upsample(ctx: SeriesContext, *, factor: int = 2, method: str = "ffill") -> Series[Price]:
    src = _select(ctx)
    if factor <= 1:
        return src
    n = len(src)
    if n == 0:
        return _empty_like(src)  # type: ignore
    # Interleave (factor-1) duplicates between points using ffill
    new_ts = []
    new_vals: list[Decimal] = []  # type: ignore[type-arg]
    for i in range(n):
        new_ts.append(src.timestamps[i])
        new_vals.append(_dec(src.values[i]))  # type: ignore
        if i < n - 1:
            for _ in range(factor - 1):
                # No real new timestamps available; reuse current for placeholder
                new_ts.append(src.timestamps[i])
                new_vals.append(_dec(src.values[i]))  # type: ignore
    res = _build_like(src, new_ts, new_vals)  # type: ignore
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=src.symbol,
        timeframe=src.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register(
    "sync_timeframe",
    description="Align a series to a reference's timestamps with ffill or linear interpolation",
)
def sync_timeframe(ctx: SeriesContext, reference: Series[Price], *, fill: str = "ffill") -> Series[Price]:
    src = _select(ctx)
    # Build values for reference timestamps using chosen method
    ref_ts = list(reference.timestamps)
    if not ref_ts:
        return _empty_like(src)  # type: ignore
    # Map original points
    src_map = {ts: _dec(v) for ts, v in zip(src.timestamps, src.values, strict=False)}  # type: ignore
    # Ensure ordered lists
    ts_list = list(src.timestamps)
    val_list = [src_map[ts] for ts in ts_list]
    out_vals: list[Decimal] = []  # type: ignore[type-arg]
    if fill == "ffill":
        last: Decimal | None = None  # type: ignore
        for ts in ref_ts:
            if ts in src_map:
                last = src_map[ts]
                out_vals.append(last)
            else:
                if last is None:
                    # seed with first value
                    last = val_list[0] if val_list else Decimal(0)
                out_vals.append(last)
    elif fill == "linear":
        # For each ref ts, if exact match use it; else interpolate between nearest in src
        from bisect import bisect_left

        for ts in ref_ts:
            if ts in src_map:
                out_vals.append(src_map[ts])
            else:
                i = bisect_left(ts_list, ts)
                if i == 0:
                    out_vals.append(val_list[0])
                elif i >= len(ts_list):
                    out_vals.append(val_list[-1])
                else:
                    t0, t1 = ts_list[i - 1], ts_list[i]
                    v0, v1 = val_list[i - 1], val_list[i]
                    # linear weight
                    total = (t1 - t0).total_seconds()
                    w = (ts - t0).total_seconds() / total if total != 0 else 0.0
                    # compute Decimal blend
                    out_vals.append(v0 + (v1 - v0) * Decimal(str(w)))
    else:
        raise ValueError("sync_timeframe fill must be 'ffill' or 'linear'")
    res = _build_like(src, ref_ts, out_vals)  # type: ignore
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=src.symbol,
        timeframe=src.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )
