from __future__ import annotations

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
    return _with_window_mask(run_kernel(src, RollingSumKernel(), min_periods=period, period=period), period)


@register(spec=_rolling_spec("rolling_mean", ("mean", "average", "avg"), "Rolling mean over a window"))
def rolling_mean(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(src, RollingMeanKernel(), min_periods=period, period=period), period)


@register(spec=_rolling_spec("rolling_std", ("std", "stddev"), "Rolling standard deviation over a window"))
def rolling_std(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(src, RollingStdKernel(), min_periods=period, period=period), period)


@register(spec=_rolling_spec("max", (), "Maximum value in a rolling window"))
def rolling_max(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(source, RollingMaxKernel(), min_periods=period, period=period), period)


@register(spec=_rolling_spec("min", (), "Minimum value in a rolling window"))
def rolling_min(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(source, RollingMinKernel(), min_periods=period, period=period), period)


@register(spec=_rolling_spec("rolling_argmax", ("argmax",), "Offset of maximum value inside a rolling window"))
def rolling_argmax(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(source, RollingArgmaxKernel(), min_periods=period, period=period), period)


@register(spec=_rolling_spec("rolling_argmin", ("argmin",), "Offset of minimum value inside a rolling window"))
def rolling_argmin(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    source = _select_field(ctx, field) if field else _select(ctx)
    return _with_window_mask(run_kernel(source, RollingArgminKernel(), min_periods=period, period=period), period)


@register(spec=_rolling_spec("rolling_median", ("median", "med"), "Median over window (O(n*w))"))
def rolling_median(ctx: SeriesContext, period: int = 20, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    return run_kernel(src, RollingMedianKernel(), min_periods=period, period=period)


@register(spec=_rolling_spec("rolling_ema", (), "Exponential Moving Average over a window"))
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
