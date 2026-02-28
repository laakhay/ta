"""Supertrend indicator using kernels."""

from __future__ import annotations

import ta_py

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...primitives.kernels.supertrend import SupertrendKernel
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)
from .._utils import results_to_series
from ..volatility.atr import atr

SUPERTREND_SPEC = IndicatorSpec(
    name="supertrend",
    description="Supertrend indicator",
    params={
        "period": ParamSpec(name="period", type=int, default=10, required=False),
        "multiplier": ParamSpec(name="multiplier", type=float, default=3.0, required=False),
    },
    outputs={
        "supertrend": OutputSpec(name="supertrend", type=Series, description="Supertrend line", role="line"),
        "direction": OutputSpec(
            name="direction", type=Series, description="Trend direction (1=bull, -1=bear)", role="line"
        ),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="supertrend"),
)


@register(spec=SUPERTREND_SPEC)
def supertrend(ctx: SeriesContext, period: int = 10, multiplier: float = 3.0) -> tuple[Series[Price], Series[Price]]:
    """
    Supertrend indicator.

    Returns (supertrend_line, direction_series).
    """
    if period <= 0:
        raise ValueError("Supertrend period must be positive")

    h, l, c = ctx.high, ctx.low, ctx.close
    if not (h and l and c) or len(c) == 0:
        empty = c.__class__(timestamps=(), values=(), symbol=c.symbol, timeframe=c.timeframe)
        return empty, empty

    if hasattr(ta_py, "supertrend"):
        st_vals, dir_vals = ta_py.supertrend(
            [float(v) for v in h.values],
            [float(v) for v in l.values],
            [float(v) for v in c.values],
            period,
            multiplier,
        )
        return (
            results_to_series(st_vals, c, value_class=Price),
            results_to_series(dir_vals, c, value_class=Price),
        )

    # Temporary fallback while ta_py upgrades.
    # Calculate ATR first
    atr_series = atr(ctx, period)

    # Zip H, L, C, and ATR
    stamps = c.timestamps
    vals_h = h.values
    vals_l = l.values
    vals_c = c.values
    vals_a = atr_series.values

    # ATR removes first period-1 bars
    warmup_len = period - 1
    xs = list(zip(vals_h, vals_l, vals_c, vals_a, strict=True))

    kernel = SupertrendKernel()
    state = kernel.initialize([], period=period, multiplier=multiplier)

    out_st = []
    out_dir = []

    for x_t in xs:
        state, (st_val, dir_val) = kernel.step(state, x_t, period=period, multiplier=multiplier)
        out_st.append(st_val)
        out_dir.append(dir_val)

    res_stamps = stamps

    return (
        CoreSeries[Price](
            timestamps=res_stamps,
            values=tuple(Price(v) for v in out_st),
            symbol=c.symbol,
            timeframe=c.timeframe,
            availability_mask=tuple(True for _ in out_st),
        ),
        CoreSeries[Price](
            timestamps=res_stamps,
            values=tuple(Price(v) for v in out_dir),
            symbol=c.symbol,
            timeframe=c.timeframe,
            availability_mask=tuple(True for _ in out_dir),
        ),
    )
