"""Primitive operations for building indicators using expressions.

This module provides low-level operations that can be composed using
the expression system to create complex indicators.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Any

from ..core import Series
from ..core.types import Price
from ..registry.models import SeriesContext
from ..registry.registry import register
from ._kernels import (
    _empty_like, _build_like, _dec, ew_unary, ew_binary, ew_scalar_right,
    rolling_kernel, rolling_sum_recipe, rolling_mean_recipe, rolling_std_recipe,
    rolling_max_deque, rolling_min_deque,
)


def _select(ctx: SeriesContext) -> Series[Price]:
    """Pick a reasonable default source series from the context."""
    for c in ("price", "close"):
        if c in ctx.available_series: 
            return getattr(ctx, c)
    if not ctx.available_series:
        raise ValueError("SeriesContext has no series to operate on")
    return getattr(ctx, ctx.available_series[0])


# ---------- rolling ----------

@register("rolling_sum", description="Rolling sum over a window")
def rolling_sum(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    src = _select(ctx)
    init, upd = rolling_sum_recipe(period)
    return rolling_kernel(src, period, init=init, update=upd)


@register("rolling_mean", description="Rolling mean over a window")
def rolling_mean(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    src = _select(ctx)
    init, upd = rolling_mean_recipe(period)
    return rolling_kernel(src, period, init=init, update=upd)


@register("rolling_std", description="Rolling standard deviation over a window")
def rolling_std(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    src = _select(ctx)
    init, upd = rolling_std_recipe(period)
    return rolling_kernel(src, period, init=init, update=upd)


@register("max", description="Maximum value in a rolling window")
def rolling_max(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    return rolling_max_deque(_select(ctx), period)


@register("min", description="Minimum value in a rolling window")
def rolling_min(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    return rolling_min_deque(_select(ctx), period)


# Fallback example (rare): rolling_median using generic window_eval
@register("rolling_median", description="Median over window (O(n*w))")
def rolling_median(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    src = _select(ctx)
    return rolling_kernel(src, period, window_eval=lambda w: sorted(w)[len(w)//2])


# ---------- element-wise ----------

@register("elementwise_max", description="Element-wise maximum of two series")
def elementwise_max(ctx: SeriesContext, other_series: Series[Price]) -> Series[Price]:
    a = _select(ctx)
    return ew_binary(a, other_series, max)


@register("elementwise_min", description="Element-wise minimum of two series")
def elementwise_min(ctx: SeriesContext, other_series: Series[Price]) -> Series[Price]:
    a = _select(ctx)
    return ew_binary(a, other_series, min)


@register("cumulative_sum", description="Cumulative sum of a series")
def cumulative_sum(ctx: SeriesContext) -> Series[Price]:
    src = _select(ctx)
    acc = Decimal(0)
    vals = []
    for v in src.values:
        acc += _dec(v)
        vals.append(acc)
    return _build_like(src, src.timestamps, vals)


@register("diff", description="Difference between consecutive values")
def diff(ctx: SeriesContext) -> Series[Price]:
    src = _select(ctx)
    if len(src) < 2: 
        return _empty_like(src)
    xs = [_dec(v) for v in src.values]
    out = [xs[i] - xs[i-1] for i in range(1, len(xs))]
    return _build_like(src, src.timestamps[1:], out)


@register("shift", description="Shift series by n periods")
def shift(ctx: SeriesContext, periods: int = 1) -> Series[Price]:
    src = _select(ctx)
    n = len(src)
    if n == 0 or periods >= n or periods <= -n: 
        return _empty_like(src)
    if periods == 0: 
        return src
    if periods > 0:
        return Series[Price](
            timestamps=src.timestamps[periods:], 
            values=src.values[periods:],
            symbol=src.symbol, 
            timeframe=src.timeframe
        )
    p = -periods
    return Series[Price](
        timestamps=src.timestamps[:-p], 
        values=src.values[:-p],
        symbol=src.symbol, 
        timeframe=src.timeframe
    )


@register("positive_values", description="Replace negatives with 0")
def positive_values(ctx: SeriesContext) -> Series[Price]:
    return ew_unary(_select(ctx), lambda x: x if x > 0 else Decimal(0))


@register("negative_values", description="Replace positives with 0")
def negative_values(ctx: SeriesContext) -> Series[Price]:
    return ew_unary(_select(ctx), lambda x: x if x < 0 else Decimal(0))


@register("rolling_ema", description="Exponential Moving Average over a window")
def rolling_ema(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    src = _select(ctx)
    if period <= 0: 
        raise ValueError("Period must be positive")
    if len(src) == 0: 
        return _empty_like(src)
    xs = [_dec(v) for v in src.values]
    alpha = Decimal(2) / Decimal(period + 1)
    ema = [xs[0]]
    for i in range(1, len(xs)):
        ema.append(alpha * xs[i] + (Decimal(1) - alpha) * ema[-1])
    return _build_like(src, src.timestamps, ema)


@register("true_range", description="True Range for ATR")
def true_range(ctx: SeriesContext) -> Series[Price]:
    for name in ("high", "low", "close"):
        if not hasattr(ctx, name):
            raise ValueError("True Range requires series: ('high','low','close')")
    h, l, c = ctx.high, ctx.low, ctx.close
    if len(c) == 0: 
        return _empty_like(c)
    out = []
    for i in range(len(c)):
        if i == 0:
            tr = _dec(h.values[i]) - _dec(l.values[i])
        else:
            hl  = _dec(h.values[i]) - _dec(l.values[i])
            hp  = abs(_dec(h.values[i]) - _dec(c.values[i-1]))
            lp  = abs(_dec(l.values[i]) - _dec(c.values[i-1]))
            tr = max(hl, hp, lp)
        out.append(tr)
    return _build_like(c, c.timestamps, out)


@register("typical_price", description="(H+L+C)/3")
def typical_price(ctx: SeriesContext) -> Series[Price]:
    for name in ("high", "low", "close"):
        if not hasattr(ctx, name):
            raise ValueError("Typical Price requires series: ('high','low','close')")
    h, l, c = ctx.high, ctx.low, ctx.close
    if len(c) == 0: 
        return _empty_like(c)
    out = [(_dec(hv) + _dec(lv) + _dec(cv))/Decimal(3) for hv, lv, cv in zip(h.values, l.values, c.values)]
    return _build_like(c, c.timestamps, out)


@register("sign", description="Sign of price changes (1, 0, -1)")
def sign(ctx: SeriesContext) -> Series[Price]:
    """Calculate sign of price changes: 1 for positive, -1 for negative, 0 for zero."""
    src = _select(ctx)
    if len(src) < 2:
        return _empty_like(src)
    
    xs = [_dec(v) for v in src.values]
    out = []
    for i in range(1, len(xs)):
        diff = xs[i] - xs[i-1]
        if diff > 0:
            out.append(Decimal(1))
        elif diff < 0:
            out.append(Decimal(-1))
        else:
            out.append(Decimal(0))
    
    return _build_like(src, src.timestamps[1:], out)