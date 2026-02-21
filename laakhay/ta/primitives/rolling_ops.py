from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from decimal import Decimal
from typing import Any, Tuple

from ..core import Series
from ..core.series import Series as CoreSeries
from ..core.types import Price
from ..registry.models import SeriesContext
from ..registry.registry import register
from .kernel import run_kernel
from .kernels.ema import EMAKernel
from .kernels.math import RMAKernel
from .kernels.rolling import (
    RollingArgmaxKernel,
    RollingArgminKernel,
    RollingMaxKernel,
    RollingMeanKernel,
    RollingMedianKernel,
    RollingMinKernel,
    RollingStdKernel,
    RollingSumKernel,
)
from .math_ops import _build_like, _dec, _empty_like
from .select import _select, _select_field

InitFn = Callable[[Iterable[Decimal]], Tuple[Any, Decimal]]
UpdateFn = Callable[[Any, Decimal, Decimal], Tuple[Any, Decimal]]
FinalizeFn = Callable[[Any], Decimal | None]


def rolling_kernel(
    src: Series[Price],
    period: int,
    *,
    init: InitFn | None = None,
    update: UpdateFn | None = None,
    finalize: FinalizeFn | None = None,
    window_eval: Callable[[Iterable[Decimal]], Decimal] | None = None,
) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    n = len(src)
    if n == 0 or n < period:
        return _empty_like(src)

    xs = [_dec(v) for v in src.values]
    out: list[Decimal] = []

    if window_eval is not None:
        for i in range(period - 1, n):
            w = xs[i - period + 1 : i + 1]
            out.append(window_eval(w))
        return _build_like(src, src.timestamps[period - 1 :], out)

    if init and update:
        state, first_val = init(xs[:period])
        out.append(first_val)
        for i in range(period, n):
            state, v = update(state, xs[i - period], xs[i])
            out.append(v)
        return _build_like(src, src.timestamps[period - 1 :], out)

    raise ValueError("rolling_kernel: supply either (init,update) or window_eval")


def rolling_sum_recipe(period: int):
    def _init(win: Iterable[Decimal]):
        s = sum(win)
        return s, s

    def _update(s: Decimal, out_v: Decimal, in_v: Decimal):
        s2 = s + in_v - out_v
        return s2, s2

    return _init, _update


def rolling_mean_recipe(period: int):
    init_s, upd_s = rolling_sum_recipe(period)

    def _init(win: Iterable[Decimal]):
        s, _ = init_s(win)
        m = s / Decimal(period)
        return s, m

    def _update(s: Decimal, out_v: Decimal, in_v: Decimal):
        s2, s2_val = upd_s(s, out_v, in_v)
        return s2, s2_val / Decimal(period)

    return _init, _update


def rolling_std_recipe(period: int):
    def _init(win: Iterable[Decimal]):
        xs = list(win)
        s = sum(xs)
        ss = sum(x * x for x in xs)
        mean = s / Decimal(period)
        var = (ss / Decimal(period)) - mean * mean
        std = var.sqrt() if var >= 0 else Decimal(0)
        return (s, ss), std

    def _update(state: Tuple[Decimal, Decimal], out_v: Decimal, in_v: Decimal):
        s, ss = state
        s2 = s + in_v - out_v
        ss2 = ss + in_v * in_v - out_v * out_v
        mean = s2 / Decimal(period)
        var = (ss2 / Decimal(period)) - mean * mean
        std = var.sqrt() if var >= 0 else Decimal(0)
        return (s2, ss2), std

    return _init, _update


def rolling_max_deque(src: Series[Price], period: int) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    n = len(src)
    if n == 0 or n < period:
        return _empty_like(src)
    xs = [_dec(v) for v in src.values]
    dq: deque[int] = deque()
    out: list[Decimal] = []
    for i, v in enumerate(xs):
        while dq and xs[dq[-1]] <= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - period:
            dq.popleft()
        if i >= period - 1:
            out.append(xs[dq[0]])
    return _build_like(src, src.timestamps[period - 1 :], out)


def rolling_min_deque(src: Series[Price], period: int) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    n = len(src)
    if n == 0 or n < period:
        return _empty_like(src)
    xs = [_dec(v) for v in src.values]
    dq: deque[int] = deque()
    out: list[Decimal] = []
    for i, v in enumerate(xs):
        while dq and xs[dq[-1]] >= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - period:
            dq.popleft()
        if i >= period - 1:
            out.append(xs[dq[0]])
    return _build_like(src, src.timestamps[period - 1 :], out)


def rolling_argmax_deque(src: Series[Price], period: int) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    n = len(src)
    if n == 0 or n < period:
        return _empty_like(src)
    xs = [_dec(v) for v in src.values]
    dq: deque[int] = deque()
    out: list[Decimal] = []
    for i, v in enumerate(xs):
        while dq and xs[dq[-1]] <= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - period:
            dq.popleft()
        if i >= period - 1:
            out.append(Decimal(i - dq[0]))
    return _build_like(src, src.timestamps[period - 1 :], out)


def rolling_argmin_deque(src: Series[Price], period: int) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    n = len(src)
    if n == 0 or n < period:
        return _empty_like(src)
    xs = [_dec(v) for v in src.values]
    dq: deque[int] = deque()
    out: list[Decimal] = []
    for i, v in enumerate(xs):
        while dq and xs[dq[-1]] >= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - period:
            dq.popleft()
        if i >= period - 1:
            out.append(Decimal(i - dq[0]))
    return _build_like(src, src.timestamps[period - 1 :], out)


def _with_window_mask(res: Series[Price], period: int) -> Series[Price]:
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


@register("rolling_sum", aliases=["sum"], description="Rolling sum over a window")
def rolling_sum(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(src, RollingSumKernel(), min_periods=period, period=period), period)


@register("rolling_mean", aliases=["mean", "average", "avg"], description="Rolling mean over a window")
def rolling_mean(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(src, RollingMeanKernel(), min_periods=period, period=period), period)


@register("rolling_std", aliases=["std", "stddev"], description="Rolling standard deviation over a window")
def rolling_std(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(src, RollingStdKernel(), min_periods=period, period=period), period)


@register("max", description="Maximum value in a rolling window")
def rolling_max(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(source, RollingMaxKernel(), min_periods=period, period=period), period)


@register("min", description="Minimum value in a rolling window")
def rolling_min(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(source, RollingMinKernel(), min_periods=period, period=period), period)


@register("rolling_argmax", aliases=["argmax"], description="Offset of maximum value inside a rolling window")
def rolling_argmax(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(source, RollingArgmaxKernel(), min_periods=period, period=period), period)


@register("rolling_argmin", aliases=["argmin"], description="Offset of minimum value inside a rolling window")
def rolling_argmin(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(source, RollingArgminKernel(), min_periods=period, period=period), period)


@register("rolling_median", aliases=["median", "med"], description="Median over window (O(n*w))")
def rolling_median(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    return run_kernel(src, RollingMedianKernel(), min_periods=period, period=period)


@register("rolling_ema", description="Exponential Moving Average over a window")
def rolling_ema(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    src = _select_field(ctx, field) if field else _select(ctx)
    res = run_kernel(src, EMAKernel(), min_periods=1, period=period)
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register("rolling_rma", aliases=["rma"], description="Wilder's Moving Average (alpha=1/period)")
def rolling_rma(ctx: SeriesContext, period: int = 14, field: str | None = None) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    src = _select_field(ctx, field) if field else _select(ctx)
    res = run_kernel(src, RMAKernel(), min_periods=1, period=period)
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


__all__ = [
    "rolling_argmax",
    "rolling_argmax_deque",
    "rolling_argmin",
    "rolling_argmin_deque",
    "rolling_ema",
    "rolling_kernel",
    "rolling_max",
    "rolling_max_deque",
    "rolling_mean",
    "rolling_mean_recipe",
    "rolling_median",
    "rolling_min",
    "rolling_min_deque",
    "rolling_rma",
    "rolling_std",
    "rolling_std_recipe",
    "rolling_sum",
    "rolling_sum_recipe",
]
