"""Ichimoku Cloud indicator implementation using primitives."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
from ...core.types import Price
from ...primitives.rolling_ops import rolling_max, rolling_min
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)

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

    # 1. Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
    tenkan_sen = (
        rolling_max(ctx, tenkan_period, field="high") + rolling_min(ctx, tenkan_period, field="low")
    ) / Decimal(2)

    # 2. Kijun-sen (Base Line): (26-period high + 26-period low) / 2
    kijun_sen = (rolling_max(ctx, kijun_period, field="high") + rolling_min(ctx, kijun_period, field="low")) / Decimal(
        2
    )

    # 3. Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2, plotted 26 periods ahead
    senkou_span_a = ((tenkan_sen + kijun_sen) / Decimal(2)).shift(displacement)

    # 4. Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, plotted 26 periods ahead
    senkou_span_b = (
        (rolling_max(ctx, span_b_period, field="high") + rolling_min(ctx, span_b_period, field="low")) / Decimal(2)
    ).shift(displacement)

    # 5. Chikou Span (Lagging Span): Current close plotted 26 periods behind
    chikou_span = ctx.close.shift(-displacement)

    return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span
