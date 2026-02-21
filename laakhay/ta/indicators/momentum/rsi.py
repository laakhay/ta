"""Relative Strength Index (RSI) indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...core.types import Price
from ...primitives.kernel import run_kernel
from ...primitives.kernels.rsi import RSIKernel
from .. import (
    SeriesContext,
    register,
)


@register("rsi", description="Relative Strength Index")
def rsi(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Relative Strength Index indicator using Wilder's Smoothing.

    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss

    Uses Wilder's Smoothing (Modified Moving Average) for average gains and losses,
    which provides smoother, more accurate RSI values compared to simple moving average.
    """
    if period <= 0:
        raise ValueError("RSI period must be positive")
    close_series = ctx.close
    if not close_series or len(close_series) <= 1:
        # Return empty series with correct meta
        return close_series.__class__(
            timestamps=(),
            values=(),
            symbol=close_series.symbol,
            timeframe=close_series.timeframe,
        )

    return run_kernel(close_series, RSIKernel(), min_periods=period + 1, period=period)
