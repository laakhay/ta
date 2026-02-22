"""MACD (Moving Average Convergence Divergence) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...primitives.rolling_ops import rolling_ema
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)
from .. import Price, SeriesContext, register

MACD_SPEC = IndicatorSpec(
    name="macd",
    description="MACD (Moving Average Convergence Divergence)",
    params={
        "fast_period": ParamSpec(name="fast_period", type=int, default=12, required=False),
        "slow_period": ParamSpec(name="slow_period", type=int, default=26, required=False),
        "signal_period": ParamSpec(name="signal_period", type=int, default=9, required=False),
    },
    outputs={
        "macd": OutputSpec(name="macd", type=Series, description="MACD line (fast EMA - slow EMA)", role="line"),
        "signal": OutputSpec(name="signal", type=Series, description="Signal line (EMA of MACD line)", role="signal"),
        "histogram": OutputSpec(
            name="histogram", type=Series, description="MACD histogram (macd - signal)", role="histogram"
        ),
    },
    semantics=SemanticsSpec(
        required_fields=("close",),
        lookback_params=("fast_period", "slow_period", "signal_period"),
        default_lookback=1,
    ),
    runtime_binding=RuntimeBindingSpec(kernel_id="macd"),
)


@register(spec=MACD_SPEC)
def macd(
    ctx: SeriesContext,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[Series[Price], Series[Price], Series[Price]]:
    """
    MACD indicator using primitives.

    Returns (macd_line, signal_line, histogram) where:
    - macd_line = EMA(fast) - EMA(slow)
    - signal_line = EMA(macd_line)
    - histogram = macd_line - signal_line
    """
    if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
        raise ValueError("MACD periods must be positive")
    if fast_period >= slow_period:
        raise ValueError("Fast period must be less than slow period")

    close = ctx.close
    if close is None or len(close) == 0:
        empty = close.__class__(timestamps=(), values=(), symbol=close.symbol, timeframe=close.timeframe)
        return empty, empty, empty

    # Calculate EMAs using rolling_ema primitive
    fast_ema = rolling_ema(ctx, fast_period)
    slow_ema = rolling_ema(ctx, slow_period)

    macd_line = fast_ema - slow_ema

    # Calculate signal line (EMA of MACD line)
    macd_ctx = SeriesContext(close=macd_line)
    signal_line = rolling_ema(macd_ctx, signal_period)

    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram
