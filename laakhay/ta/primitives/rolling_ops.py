from __future__ import annotations

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
from .select import _select, _select_field


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
    "rolling_argmin",
    "rolling_ema",
    "rolling_max",
    "rolling_mean",
    "rolling_median",
    "rolling_min",
    "rolling_rma",
    "rolling_std",
    "rolling_sum",
]
