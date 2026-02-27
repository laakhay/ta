from __future__ import annotations

import math

import ta_py

from ..core import Series
from ..core.series import Series as CoreSeries
from ..core.types import Price
from ..registry.models import SeriesContext
from ..registry.registry import register
from ..registry.schemas import (
    IndicatorSpec,
    InputSlotSpec,
    OutputSpec,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)
from .kernel import run_kernel
from .kernels.rolling import (
    RollingArgmaxKernel,
    RollingArgminKernel,
    RollingMedianKernel,
)
from .select import _select, _select_field


def _series_to_f64(src: Series[Price]) -> list[float]:
    return [float(v) for v in src.values]


def _f64_to_series(src: Series[Price], values: list[float]) -> Series[Price]:
    return CoreSeries[Price](
        timestamps=src.timestamps,
        values=tuple(Price("NaN") if math.isnan(v) else Price(str(v)) for v in values),
        symbol=src.symbol,
        timeframe=src.timeframe,
    )


def _with_window_mask(res: Series[Price], period: int, src: Series | None = None) -> Series[Price]:
    if len(res) == 0:
        return res

    # Calculate window mask based on period
    window_mask = [False] * len(res)
    for i in range(len(res)):
        if i >= period - 1:
            window_mask[i] = True

            # If source has a mask, the result is only available if ALL values in the window were available
            if src and src.availability_mask:
                for j in range(i - period + 1, i + 1):
                    if not src.availability_mask[j]:
                        window_mask[i] = False
                        break

    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(window_mask),
    )


def _rolling_spec(name: str, aliases: tuple[str, ...], description: str) -> IndicatorSpec:
    return IndicatorSpec(
        name=name,
        description=description,
        aliases=aliases,
        inputs=(InputSlotSpec(name="field", required=False, default_source="ohlcv", default_field="close"),),
        params={
            "period": ParamSpec(name="period", type=int, default=20, required=False),
            "field": ParamSpec(name="field", type=str, default=None, required=False),
        },
        outputs={"result": OutputSpec(name="result", type=Series, description="Rolling result", role="line")},
        semantics=SemanticsSpec(
            required_fields=("close",), lookback_params=("period",), input_field="close", input_series_param="field"
        ),
        runtime_binding=RuntimeBindingSpec(kernel_id=name),
        param_aliases={"lookback": "period"},
    )


@register(spec=_rolling_spec("rolling_sum", ("sum",), "Rolling sum over a window"))
def rolling_sum(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    if period <= 0:
        raise ValueError("Period must be positive")
    res = _f64_to_series(src, ta_py.rolling_sum(_series_to_f64(src), period))
    return _with_window_mask(res, period, src=src)


@register(spec=_rolling_spec("rolling_mean", ("mean", "average", "avg"), "Rolling mean over a window"))
def rolling_mean(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    if period <= 0:
        raise ValueError("Period must be positive")
    res = _f64_to_series(src, ta_py.rolling_mean(_series_to_f64(src), period))
    return _with_window_mask(res, period, src=src)


@register(spec=_rolling_spec("rolling_std", ("std", "stddev"), "Rolling standard deviation over a window"))
def rolling_std(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    if period <= 0:
        raise ValueError("Period must be positive")
    res = _f64_to_series(src, ta_py.rolling_std(_series_to_f64(src), period))
    return _with_window_mask(res, period, src=src)


@register(spec=_rolling_spec("max", (), "Maximum value in a rolling window"))
def rolling_max(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    if period <= 0:
        raise ValueError("Period must be positive")
    res = _f64_to_series(source, ta_py.rolling_max(_series_to_f64(source), period))
    return _with_window_mask(res, period, src=source)


@register(spec=_rolling_spec("min", (), "Minimum value in a rolling window"))
def rolling_min(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    if period <= 0:
        raise ValueError("Period must be positive")
    res = _f64_to_series(source, ta_py.rolling_min(_series_to_f64(source), period))
    return _with_window_mask(res, period, src=source)


@register(spec=_rolling_spec("rolling_argmax", ("argmax",), "Offset of maximum value inside a rolling window"))
def rolling_argmax(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    res = run_kernel(source, RollingArgmaxKernel(), min_periods=period, period=period)
    return _with_window_mask(res, period, src=source)


@register(spec=_rolling_spec("rolling_argmin", ("argmin",), "Offset of minimum value inside a rolling window"))
def rolling_argmin(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    res = run_kernel(source, RollingArgminKernel(), min_periods=period, period=period)
    return _with_window_mask(res, period, src=source)


@register(spec=_rolling_spec("rolling_median", ("median", "med"), "Median over window (O(n*w))"))
def rolling_median(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    return run_kernel(src, RollingMedianKernel(), min_periods=period, period=period)


@register(spec=_rolling_spec("rolling_ema", (), "Exponential Moving Average over a window"))
def rolling_ema(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    src = _select_field(ctx, field) if field else _select(ctx)
    res = _f64_to_series(src, ta_py.rolling_ema(_series_to_f64(src), period))

    # EMA is technically available from index 0, but we should respect source mask
    final_mask = tuple(True for _ in res.values)
    if src.availability_mask:
        from ..core.series import _and_masks

        final_mask = _and_masks(final_mask, src.availability_mask)

    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=final_mask,
    )


_ROLLING_RMA_SPEC = IndicatorSpec(
    name="rolling_rma",
    description="Wilder's Moving Average (alpha=1/period)",
    aliases=("rma",),
    inputs=(InputSlotSpec(name="field", required=False, default_source="ohlcv", default_field="close"),),
    params={
        "period": ParamSpec(name="period", type=int, default=14, required=False),
        "field": ParamSpec(name="field", type=str, default=None, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="RMA values", role="line")},
    semantics=SemanticsSpec(
        required_fields=("close",), lookback_params=("period",), input_field="close", input_series_param="field"
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="rolling_rma"),
    param_aliases={"lookback": "period"},
)


@register(spec=_ROLLING_RMA_SPEC)
def rolling_rma(ctx: SeriesContext, period: int = 14, field: str | None = None) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    src = _select_field(ctx, field) if field else _select(ctx)
    res = _f64_to_series(src, ta_py.rolling_rma(_series_to_f64(src), period))

    final_mask = tuple(True for _ in res.values)
    if src.availability_mask:
        from ..core.series import _and_masks

        final_mask = _and_masks(final_mask, src.availability_mask)

    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=final_mask,
    )


@register(spec=_rolling_spec("rolling_wma", ("wma",), "Weighted Moving Average over a window"))
def rolling_wma(ctx: SeriesContext, period: int = 14, field: str | None = None) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    src = _select_field(ctx, field) if field else _select(ctx)
    res = _f64_to_series(src, ta_py.rolling_wma(_series_to_f64(src), period))
    return _with_window_mask(res, period, src=src)


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
    "rolling_wma",
]
