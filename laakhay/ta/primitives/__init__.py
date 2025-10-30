"""Primitive operations for building indicators using expressions.

This module provides low-level operations that can be composed using
the expression system to create complex indicators.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Any, Callable, Iterable, Tuple

from ..core import Series
from ..core.types import Price
from ..registry.models import SeriesContext
from ..registry.registry import register
from ..core.series import Series as CoreSeries

# Import kernel functions with proper type annotations
from ._kernels import (  # type: ignore
    _empty_like,  # type: ignore
    _build_like,  # type: ignore
    _dec,  # type: ignore
    ew_unary,  # type: ignore
    ew_binary,  # type: ignore
    rolling_kernel,  # type: ignore
    rolling_sum_recipe,  # type: ignore
    rolling_mean_recipe,  # type: ignore
    rolling_std_recipe,  # type: ignore
    rolling_max_deque,  # type: ignore
    rolling_min_deque,  # type: ignore
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
    init: InitFn
    upd: UpdateFn
    init, upd = rolling_sum_recipe(period)  # type: ignore
    res = rolling_kernel(src, period, init=init, update=upd)  # type: ignore
    # availability: first period-1 values are not valid
    if len(res) == 0:
        return res
    mask = tuple((i >= period - 1) for i in range(len(res)))
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=mask)


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
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=mask)


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
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=mask)


@register("max", description="Maximum value in a rolling window")
def rolling_max(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    res = rolling_max_deque(_select(ctx), period)  # type: ignore
    if len(res) == 0:
        return res
    mask = tuple((i >= period - 1) for i in range(len(res)))
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=mask)


@register("min", description="Minimum value in a rolling window")
def rolling_min(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    res = rolling_min_deque(_select(ctx), period)  # type: ignore
    if len(res) == 0:
        return res
    mask = tuple((i >= period - 1) for i in range(len(res)))
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=mask)


# Fallback example (rare): rolling_median using generic window_eval
@register("rolling_median", description="Median over window (O(n*w))")
def rolling_median(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    src = _select(ctx)
    return rolling_kernel(src, period, window_eval=lambda w: sorted(w)[len(w)//2])  # type: ignore


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
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=tuple(True for _ in res.values))


@register("diff", description="Difference between consecutive values")
def diff(ctx: SeriesContext) -> Series[Price]:
    src = _select(ctx)
    if len(src) < 2: 
        return _empty_like(src)  # type: ignore
    xs = [_dec(v) for v in src.values]  # type: ignore
    out = [xs[i] - xs[i-1] for i in range(1, len(xs))]  # type: ignore
    res = _build_like(src, src.timestamps[1:], out)  # type: ignore
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=tuple(True for _ in res.values))


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
            timeframe=src.timeframe
        )
        return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=tuple(True for _ in res.values))
    p = -periods
    res = Series[Price](
        timestamps=src.timestamps[:-p], 
        values=src.values[:-p],
        symbol=src.symbol, 
        timeframe=src.timeframe
    )
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=tuple(True for _ in res.values))


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
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=tuple(True for _ in res.values))


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
            hl  = _dec(h.values[i]) - _dec(l.values[i])  # type: ignore
            hp  = abs(_dec(h.values[i]) - _dec(c.values[i-1]))  # type: ignore
            lp  = abs(_dec(l.values[i]) - _dec(c.values[i-1]))  # type: ignore
            tr = max(hl, hp, lp)  # type: ignore
        out.append(tr)  # type: ignore
    res = _build_like(c, c.timestamps, out)  # type: ignore
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=tuple(True for _ in res.values))


@register("typical_price", description="(H+L+C)/3")
def typical_price(ctx: SeriesContext) -> Series[Price]:
    for name in ("high", "low", "close"):
        if not hasattr(ctx, name):
            raise ValueError("Typical Price requires series: ('high','low','close')")
    h, l, c = ctx.high, ctx.low, ctx.close
    if len(c) == 0: 
        return _empty_like(c)  # type: ignore
    out = [(_dec(hv) + _dec(lv) + _dec(cv))/Decimal(3) for hv, lv, cv in zip(h.values, l.values, c.values)]  # type: ignore
    res = _build_like(c, c.timestamps, out)  # type: ignore
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=tuple(True for _ in res.values))


@register("sign", description="Sign of price changes (1, 0, -1)")
def sign(ctx: SeriesContext) -> Series[Price]:
    """Calculate sign of price changes: 1 for positive, -1 for negative, 0 for zero."""
    src = _select(ctx)
    if len(src) < 2:
        return _empty_like(src)  # type: ignore
    
    xs = [_dec(v) for v in src.values]  # type: ignore
    out = []  # type: ignore
    for i in range(1, len(xs)):  # type: ignore
        diff = xs[i] - xs[i-1]  # type: ignore
        if diff > 0:
            out.append(Decimal(1))  # type: ignore
        elif diff < 0:
            out.append(Decimal(-1))  # type: ignore
        else:
            out.append(Decimal(0))  # type: ignore
    
    res = _build_like(src, src.timestamps[1:], out)  # type: ignore
    return CoreSeries[Price](timestamps=res.timestamps, values=res.values, symbol=res.symbol, timeframe=res.timeframe, availability_mask=tuple(True for _ in res.values))
