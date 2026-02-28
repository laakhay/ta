from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

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
from .kernels.math import (
    AbsoluteValueKernel,
    CumulativeSumKernel,
    DiffKernel,
    NegativeKernel,
    PairMaxKernel,
    PairMinKernel,
    PassthroughKernel,
    PositiveKernel,
    SignKernel,
    TrueRangeKernel,
    TypicalPriceKernel,
)
from .math_ops import _build_like, _dec, _empty_like
from .select import _select, _select_field


def _series_to_epoch_millis(src: Series[Price]) -> list[int]:
    return [int(ts.timestamp() * 1000) for ts in src.timestamps]


def _epoch_millis_to_timestamps(values: list[int]) -> list[datetime]:
    return [datetime.fromtimestamp(v / 1000, tz=UTC) for v in values]


def _f64_to_decimals(values: list[float]) -> list[Decimal]:
    return [Decimal("NaN") if str(v) == "nan" else Decimal(str(v)) for v in values]


def _zip_binary_series(a: Series[Price], b: Series[Price]) -> Series[Any]:
    if a.symbol != b.symbol or a.timeframe != b.timeframe:
        raise ValueError("mismatched metadata (symbol/timeframe)")
    if len(a) != len(b) or a.timestamps != b.timestamps:
        raise ValueError("timestamp alignment mismatch")
    vals = tuple((_dec(x), _dec(y)) for x, y in zip(a.values, b.values, strict=True))
    return Series[Any](timestamps=a.timestamps, values=vals, symbol=a.symbol, timeframe=a.timeframe)


def _zip_hlc_series(high: Series[Price], low: Series[Price], close: Series[Price]) -> Series[Any]:
    if not (high.symbol == low.symbol == close.symbol and high.timeframe == low.timeframe == close.timeframe):
        raise ValueError("mismatched metadata (symbol/timeframe)")
    if not (high.timestamps == low.timestamps == close.timestamps):
        raise ValueError("timestamp alignment mismatch")
    vals = tuple((_dec(h), _dec(l), _dec(c)) for h, l, c in zip(high.values, low.values, close.values, strict=True))
    return Series[Any](timestamps=high.timestamps, values=vals, symbol=high.symbol, timeframe=high.timeframe)


def _elem_spec(name: str, sem: SemanticsSpec, **kw: Any) -> IndicatorSpec:
    return IndicatorSpec(
        name=name,
        params=kw.get("params", {}),
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=sem,
        runtime_binding=RuntimeBindingSpec(kernel_id=name),
        **{k: v for k, v in kw.items() if k != "params"},
    )


@register(
    spec=_elem_spec(
        "elementwise_max",
        SemanticsSpec(required_fields=("close",), optional_fields=("other_series",), default_lookback=1),
    )
)
def elementwise_max(ctx: SeriesContext, other_series: Series[Price]) -> Series[Price]:
    src = _select(ctx)
    pair_series = _zip_binary_series(src, other_series)
    return run_kernel(pair_series, PairMaxKernel(), min_periods=1, coerce_input=lambda x: x)


@register(
    spec=_elem_spec(
        "elementwise_min",
        SemanticsSpec(required_fields=("close",), optional_fields=("other_series",), default_lookback=1),
    )
)
def elementwise_min(ctx: SeriesContext, other_series: Series[Price]) -> Series[Price]:
    src = _select(ctx)
    pair_series = _zip_binary_series(src, other_series)
    return run_kernel(pair_series, PairMinKernel(), min_periods=1, coerce_input=lambda x: x)


@register(
    spec=IndicatorSpec(
        name="cumulative_sum",
        description="Cumulative sum of a series",
        aliases=("cumsum",),
        params={"field": ParamSpec("field", str, default=None, required=False)},
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(required_fields=("close",), optional_fields=(), lookback_params=(), default_lookback=1),
        runtime_binding=RuntimeBindingSpec(kernel_id="cumulative_sum"),
    )
)
def cumulative_sum(ctx: SeriesContext, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    res = run_kernel(src, CumulativeSumKernel(), min_periods=1)
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register(
    spec=IndicatorSpec(
        name="diff",
        description="Difference between consecutive values",
        params={"field": ParamSpec("field", str, default=None, required=False)},
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(required_fields=("close",), optional_fields=(), lookback_params=(), default_lookback=2),
        runtime_binding=RuntimeBindingSpec(kernel_id="diff"),
    )
)
def diff(ctx: SeriesContext, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    res = run_kernel(src, DiffKernel(), min_periods=2)
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register(
    spec=IndicatorSpec(
        name="shift",
        description="Shift series by n periods",
        params={
            "periods": ParamSpec("periods", int, default=1, required=False),
            "field": ParamSpec("field", str, default=None, required=False),
        },
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(
            required_fields=("close",), optional_fields=(), lookback_params=("periods",), default_lookback=1
        ),
        runtime_binding=RuntimeBindingSpec(kernel_id="shift"),
    )
)
def shift(ctx: SeriesContext, periods: int = 1, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    n = len(src)
    if n == 0 or periods >= n or periods <= -n:
        return _empty_like(src)
    if periods == 0:
        return src
    if periods > 0:
        res = run_kernel(src, PassthroughKernel(), min_periods=periods + 1)
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


@register(
    spec=IndicatorSpec(
        name="positive_values",
        description="Replace negatives with 0",
        aliases=("pos", "positive"),
        params={"field": ParamSpec("field", str, default=None, required=False)},
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(required_fields=("close",), optional_fields=(), default_lookback=1),
        runtime_binding=RuntimeBindingSpec(kernel_id="positive_values"),
    )
)
def positive_values(ctx: SeriesContext, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    return run_kernel(src, PositiveKernel(), min_periods=1)


@register(
    spec=IndicatorSpec(
        name="negative_values",
        description="Replace positives with 0",
        aliases=("neg", "negative"),
        params={"field": ParamSpec("field", str, default=None, required=False)},
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(required_fields=("close",), optional_fields=(), default_lookback=1),
        runtime_binding=RuntimeBindingSpec(kernel_id="negative_values"),
    )
)
def negative_values(ctx: SeriesContext, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    return run_kernel(src, NegativeKernel(), min_periods=1)


@register(
    spec=IndicatorSpec(
        name="abs",
        description="Absolute value of a series",
        params={"field": ParamSpec("field", str, default=None, required=False)},
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(required_fields=("close",), optional_fields=(), default_lookback=1),
        runtime_binding=RuntimeBindingSpec(kernel_id="abs"),
    )
)
def absolute_value(ctx: SeriesContext, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    return run_kernel(src, AbsoluteValueKernel(), min_periods=1)


@register(
    spec=IndicatorSpec(
        name="true_range",
        description="True Range for ATR",
        aliases=("tr",),
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(required_fields=("high", "low", "close"), optional_fields=(), default_lookback=2),
        runtime_binding=RuntimeBindingSpec(kernel_id="true_range"),
    )
)
def true_range(ctx: SeriesContext) -> Series[Price]:
    for name in ("high", "low", "close"):
        if not hasattr(ctx, name):
            raise ValueError("True Range requires series: ('high','low','close')")
    h, l, c = ctx.high, ctx.low, ctx.close
    if len(c) == 0:
        return _empty_like(c)
    hlc_series = _zip_hlc_series(h, l, c)
    res = run_kernel(hlc_series, TrueRangeKernel(), min_periods=1, coerce_input=lambda x: x)
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register(
    spec=IndicatorSpec(
        name="typical_price",
        description="(H+L+C)/3",
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(required_fields=("high", "low", "close"), optional_fields=(), default_lookback=1),
        runtime_binding=RuntimeBindingSpec(kernel_id="typical_price"),
    )
)
def typical_price(ctx: SeriesContext) -> Series[Price]:
    for name in ("high", "low", "close"):
        if not hasattr(ctx, name):
            raise ValueError("Typical Price requires series: ('high','low','close')")
    h, l, c = ctx.high, ctx.low, ctx.close
    if len(c) == 0:
        return _empty_like(c)
    hlc_series = _zip_hlc_series(h, l, c)
    res = run_kernel(hlc_series, TypicalPriceKernel(), min_periods=1, coerce_input=lambda x: x)
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register(
    spec=IndicatorSpec(
        name="sign",
        description="Sign of price changes (1, 0, -1)",
        params={"field": ParamSpec("field", str, default=None, required=False)},
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(required_fields=("close",), optional_fields=(), default_lookback=2),
        runtime_binding=RuntimeBindingSpec(kernel_id="sign"),
    )
)
def sign(ctx: SeriesContext, field: str | None = None) -> Series[Price]:
    src = _select_field(ctx, field) if field else _select(ctx)
    res = run_kernel(src, SignKernel(), min_periods=2)
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=res.symbol,
        timeframe=res.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register(
    spec=IndicatorSpec(
        name="downsample",
        description="Downsample by factor with aggregation. For OHLCV, uses O/H/L/C/V rules.",
        params={
            "factor": ParamSpec("factor", int, default=2, required=False),
            "agg": ParamSpec("agg", str, default="last", required=False),
            "target": ParamSpec("target", str, default="close", required=False),
            "target_timeframe": ParamSpec("target_timeframe", str, default=None, required=False),
        },
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(required_fields=("close",), optional_fields=(), default_lookback=1),
        runtime_binding=RuntimeBindingSpec(kernel_id="downsample"),
    )
)
def downsample(
    ctx: SeriesContext,
    *,
    factor: int = 2,
    agg: str = "last",
    target: str = "close",
    target_timeframe: str | None = None,
) -> Series[Price] | dict[str, Series[Price]]:
    has_ohlc = all(hasattr(ctx, k) for k in ("open", "high", "low", "close"))
    if target == "ohlcv" and has_ohlc:
        o, h, l, c = ctx.open, ctx.high, ctx.low, ctx.close
        v = getattr(ctx, "volume", None)
        n = len(c)
        if factor <= 1 or n == 0:
            result: dict[str, Series[Price]] = {"open": o, "high": h, "low": l, "close": c}
            if v is not None:
                result["volume"] = v
            return result
        result_tf = target_timeframe or c.timeframe
        ts_epoch = _series_to_epoch_millis(c)
        out_ts_epoch, o_vals_raw = ta_py.series_downsample(ts_epoch, [float(x) for x in o.values], factor, "first")
        _, h_vals_raw = ta_py.series_downsample(ts_epoch, [float(x) for x in h.values], factor, "max")
        _, l_vals_raw = ta_py.series_downsample(ts_epoch, [float(x) for x in l.values], factor, "min")
        _, c_vals_raw = ta_py.series_downsample(ts_epoch, [float(x) for x in c.values], factor, "last")
        new_ts = _epoch_millis_to_timestamps(out_ts_epoch)
        o_vals = _f64_to_decimals(o_vals_raw)
        h_vals = _f64_to_decimals(h_vals_raw)
        l_vals = _f64_to_decimals(l_vals_raw)
        c_vals = _f64_to_decimals(c_vals_raw)
        v_vals = None
        if v is not None:
            _, v_vals_raw = ta_py.series_downsample(ts_epoch, [float(x) for x in v.values], factor, "sum")
            v_vals = _f64_to_decimals(v_vals_raw)
        o_ser = _build_like(o, new_ts, o_vals)
        h_ser = _build_like(h, new_ts, h_vals)
        l_ser = _build_like(l, new_ts, l_vals)
        c_ser = _build_like(c, new_ts, c_vals)
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
            v_ser = _build_like(v, new_ts, v_vals)
            res["volume"] = CoreSeries[Price](
                timestamps=v_ser.timestamps,
                values=v_ser.values,
                symbol=v.symbol,
                timeframe=result_tf,
                availability_mask=tuple(True for _ in v_ser.values),
            )
        return res

    src = _select(ctx)
    if factor <= 1:
        return src
    n = len(src)
    if n == 0:
        return _empty_like(src)
    out_ts_epoch, out_vals_raw = ta_py.series_downsample(
        _series_to_epoch_millis(src),
        [float(v) for v in src.values],
        factor,
        agg,
    )
    res = _build_like(src, _epoch_millis_to_timestamps(out_ts_epoch), _f64_to_decimals(out_vals_raw))
    result_tf = target_timeframe or src.timeframe
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=src.symbol,
        timeframe=result_tf,
        availability_mask=tuple(True for _ in res.values),
    )


@register(
    spec=IndicatorSpec(
        name="upsample",
        description="Upsample a series by integer factor with forward-fill",
        params={
            "factor": ParamSpec("factor", int, default=2, required=False),
            "method": ParamSpec("method", str, default="ffill", required=False),
        },
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(required_fields=("close",), optional_fields=(), default_lookback=1),
        runtime_binding=RuntimeBindingSpec(kernel_id="upsample"),
    )
)
def upsample(ctx: SeriesContext, *, factor: int = 2, method: str = "ffill") -> Series[Price]:
    src = _select(ctx)
    if method != "ffill":
        raise ValueError(f"Unsupported upsample method: {method}")
    if factor <= 1:
        return src
    n = len(src)
    if n == 0:
        return _empty_like(src)
    out_ts_epoch, out_vals_raw = ta_py.series_upsample_ffill(
        _series_to_epoch_millis(src),
        [float(v) for v in src.values],
        factor,
    )
    res = _build_like(src, _epoch_millis_to_timestamps(out_ts_epoch), _f64_to_decimals(out_vals_raw))
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=src.symbol,
        timeframe=src.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


@register(
    spec=IndicatorSpec(
        name="sync_timeframe",
        description="Align a series to a reference's timestamps with ffill or linear interpolation",
        inputs=(InputSlotSpec("reference", "Reference series for timestamp alignment", required=True),),
        params={"fill": ParamSpec("fill", str, default="ffill", required=False)},
        outputs={"result": OutputSpec(name="result", type=Series, description="Result", role="line")},
        semantics=SemanticsSpec(required_fields=("close",), optional_fields=(), default_lookback=1),
        runtime_binding=RuntimeBindingSpec(kernel_id="sync_timeframe"),
    )
)
def sync_timeframe(ctx: SeriesContext, reference: Series[Price], *, fill: str = "ffill") -> Series[Price]:
    src = _select(ctx)
    ref_ts = list(reference.timestamps)
    if not ref_ts:
        return _empty_like(src)
    out_vals_raw = ta_py.series_sync_timeframe(
        _series_to_epoch_millis(src),
        [float(v) for v in src.values],
        _series_to_epoch_millis(reference),
        fill,
    )
    res = _build_like(src, ref_ts, _f64_to_decimals(out_vals_raw))
    return CoreSeries[Price](
        timestamps=res.timestamps,
        values=res.values,
        symbol=src.symbol,
        timeframe=src.timeframe,
        availability_mask=tuple(True for _ in res.values),
    )


__all__ = [
    "absolute_value",
    "cumulative_sum",
    "downsample",
    "diff",
    "elementwise_max",
    "elementwise_min",
    "negative_values",
    "positive_values",
    "shift",
    "sign",
    "true_range",
    "typical_price",
    "sync_timeframe",
    "upsample",
]
