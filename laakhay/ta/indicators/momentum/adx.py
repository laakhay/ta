"""Average Directional Index (ADX) indicator using kernels."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...primitives.elementwise_ops import _zip_hlc_series
from ...primitives.kernels.adx import ADXKernel
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)

ADX_SPEC = IndicatorSpec(
    name="adx",
    description="Average Directional Index (ADX) including +DI and -DI",
    params={"period": ParamSpec(name="period", type=int, default=14, required=False)},
    outputs={
        "adx": OutputSpec(name="adx", type=Series, description="ADX values", role="line"),
        "plus_di": OutputSpec(name="plus_di", type=Series, description="+DI values", role="line"),
        "minus_di": OutputSpec(name="minus_di", type=Series, description="-DI values", role="line"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("period",),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="adx"),
    param_aliases={"lookback": "period"},
)


@register(spec=ADX_SPEC)
def adx(ctx: SeriesContext, period: int = 14) -> tuple[Series[Price], Series[Price], Series[Price]]:
    """
    Average Directional Index (ADX) indicator.

    Returns (adx, plus_di, minus_di).
    ADX measures trend strength, while +DI and -DI indicate trend direction.
    """
    if period <= 0:
        raise ValueError("ADX period must be positive")

    h, l, c = ctx.high, ctx.low, ctx.close
    if not (h and l and c) or len(c) == 0:
        empty = c.__class__(timestamps=(), values=(), symbol=c.symbol, timeframe=c.timeframe)
        return empty, empty, empty

    hlc_series = _zip_hlc_series(h, l, c)

    # We run the kernel manually to capture multi-series output efficiently
    kernel = ADXKernel()
    n = len(hlc_series.values)

    # Standard Wilder's approach starts producing values after 'period' bars
    # However, to match our RMA implementation which starts immediately:
    min_periods = 1

    xs = [tuple(Decimal(str(v)) for v in val) for val in hlc_series.values]

    out_adx = []
    out_pdi = []
    out_mdi = []

    warmup_len = min_periods - 1
    state = kernel.initialize(xs[:warmup_len], period=period)

    for i in range(warmup_len, n):
        state, (adx_val, pdi_val, mdi_val) = kernel.step(state, xs[i], period=period)
        out_adx.append(adx_val)
        out_pdi.append(pdi_val)
        out_mdi.append(mdi_val)

    stamps = hlc_series.timestamps[warmup_len:]

    return (
        CoreSeries[Price](
            timestamps=stamps,
            values=tuple(Price(v) for v in out_adx),
            symbol=c.symbol,
            timeframe=c.timeframe,
            availability_mask=tuple(True for _ in out_adx),
        ),
        CoreSeries[Price](
            timestamps=stamps,
            values=tuple(Price(v) for v in out_pdi),
            symbol=c.symbol,
            timeframe=c.timeframe,
            availability_mask=tuple(True for _ in out_pdi),
        ),
        CoreSeries[Price](
            timestamps=stamps,
            values=tuple(Price(v) for v in out_mdi),
            symbol=c.symbol,
            timeframe=c.timeframe,
            availability_mask=tuple(True for _ in out_mdi),
        ),
    )
