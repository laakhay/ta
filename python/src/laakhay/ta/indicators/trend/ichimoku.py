"""Ichimoku Cloud indicator implementation using primitives."""

from __future__ import annotations

import ta_py

from ...core import Series
from ...core.types import Price
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

ICHIMOKU_SPEC = IndicatorSpec(
    name="ichimoku",
    description="Ichimoku Cloud (Ichimoku Kinko Hyo)",
    params={
        "tenkan_period": ParamSpec(name="tenkan_period", type=int, default=9, required=False),
        "kijun_period": ParamSpec(name="kijun_period", type=int, default=26, required=False),
        "span_b_period": ParamSpec(name="span_b_period", type=int, default=52, required=False),
        "displacement": ParamSpec(name="displacement", type=int, default=26, required=False),
    },
    outputs={
        "tenkan_sen": OutputSpec(name="tenkan_sen", type=Series, description="Conversion Line", role="line"),
        "kijun_sen": OutputSpec(name="kijun_sen", type=Series, description="Base Line", role="line"),
        "senkou_span_a": OutputSpec(name="senkou_span_a", type=Series, description="Leading Span A", role="line"),
        "senkou_span_b": OutputSpec(name="senkou_span_b", type=Series, description="Leading Span B", role="line"),
        "chikou_span": OutputSpec(name="chikou_span", type=Series, description="Lagging Span", role="line"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("tenkan_period", "kijun_period", "span_b_period"),
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="ichimoku"),
)


@register(spec=ICHIMOKU_SPEC)
def ichimoku(
    ctx: SeriesContext,
    tenkan_period: int = 9,
    kijun_period: int = 26,
    span_b_period: int = 52,
    displacement: int = 26,
) -> tuple[Series[Price], Series[Price], Series[Price], Series[Price], Series[Price]]:
    """
    Ichimoku Cloud indicator.

    Returns (tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span).
    """
    if tenkan_period <= 0 or kijun_period <= 0 or span_b_period <= 0 or displacement <= 0:
        raise ValueError("Ichimoku periods and displacement must be positive")

    tenkan, kijun, span_a, span_b, chikou = ta_py.ichimoku(
        [float(v) for v in ctx.high.values],
        [float(v) for v in ctx.low.values],
        [float(v) for v in ctx.close.values],
        tenkan_period,
        kijun_period,
        span_b_period,
        displacement,
    )
    return (
        results_to_series(tenkan, ctx.close, value_class=Price),
        results_to_series(kijun, ctx.close, value_class=Price),
        results_to_series(span_a, ctx.close, value_class=Price),
        results_to_series(span_b, ctx.close, value_class=Price),
        results_to_series(chikou, ctx.close, value_class=Price),
    )
