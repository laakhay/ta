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

    import ta_py
    from .._utils import results_to_series

    adx_val, pdi_val, mdi_val = ta_py.adx(
        [float(v) for v in ctx.high.values],
        [float(v) for v in ctx.low.values],
        [float(v) for v in ctx.close.values],
        period,
    )

    adx_series = results_to_series(adx_val, ctx.close, value_class=Price)
    plus_di = results_to_series(pdi_val, ctx.close, value_class=Price)
    minus_di = results_to_series(mdi_val, ctx.close, value_class=Price)

    return adx_series, plus_di, minus_di
