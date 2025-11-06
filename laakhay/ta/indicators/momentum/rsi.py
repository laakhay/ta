"""Relative Strength Index (RSI) indicator using primitives."""

from __future__ import annotations

from .. import (
    register,
    SeriesContext,
    Price,
    Expression,
    Literal,
    diff,
    negative_values,
    positive_values,
    rolling_mean,
)


@register("rsi", description="Relative Strength Index")
def rsi(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Relative Strength Index indicator using primitives.

    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    """
    if period <= 0:
        raise ValueError("RSI period must be positive")
    close_series = ctx.close
    if close_series is None or len(close_series) <= 1 or len(close_series) < period:
        # Return empty series with correct meta
        return close_series.__class__(
            timestamps=(),
            values=(),
            symbol=close_series.symbol,
            timeframe=close_series.timeframe,
        )
    # Calculate price changes and separate gains/losses
    price_changes = diff(ctx)
    gains = positive_values(SeriesContext(close=price_changes))
    losses = negative_values(SeriesContext(close=price_changes))

    # Calculate average gains and losses
    avg_gains = rolling_mean(SeriesContext(close=gains), period)
    avg_losses = rolling_mean(SeriesContext(close=losses), period)

    # Calculate RSI: 100 - (100 / (1 + RS))
    # RS = avg_gains / avg_losses (with epsilon to avoid division by zero)
    gains_expr = Expression(Literal(avg_gains))
    losses_expr = Expression(Literal(avg_losses))

    rs_expr = gains_expr / (losses_expr + 1e-10)
    rsi_expr = 100 - (100 / (1 + rs_expr))

    return rsi_expr.evaluate({})
