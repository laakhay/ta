"""Relative Strength Index (RSI) indicator using primitives."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from .. import (
    SeriesContext,
    diff,
    negative_values,
    positive_values,
    register,
)


def _wilder_smoothing(src: Series[Price], period: int) -> Series[Price]:
    """
    Apply Wilder's Smoothing (Modified Moving Average) to a series.

    Wilder's Smoothing formula:
    - First value: Simple Moving Average of first 'period' values
    - Subsequent values: (Previous Average × (Period - 1) + Current Value) / Period

    This is equivalent to EMA with alpha = 1/period, which gives smoother
    results than standard EMA for RSI calculations.
    """
    if period <= 0:
        raise ValueError("Period must be positive")
    if len(src) == 0:
        return CoreSeries[Price](
            timestamps=(),
            values=(),
            symbol=src.symbol,
            timeframe=src.timeframe,
        )
    if len(src) < period:
        return CoreSeries[Price](
            timestamps=(),
            values=(),
            symbol=src.symbol,
            timeframe=src.timeframe,
        )

    # Convert values to Decimal
    xs = [Decimal(str(v)) for v in src.values]
    out: list[Decimal] = []

    # First value: Simple Moving Average of first 'period' values
    first_avg = sum(xs[:period]) / Decimal(period)
    out.append(first_avg)

    # Subsequent values: Wilder's Smoothing
    # avg = (prev_avg * (period - 1) + current) / period
    for i in range(period, len(xs)):
        prev_avg = out[-1]
        current = xs[i]
        new_avg = (prev_avg * Decimal(period - 1) + current) / Decimal(period)
        out.append(new_avg)

    # Build result series with timestamps starting from period-1 (first valid RSI point)
    return CoreSeries[Price](
        timestamps=src.timestamps[period - 1 :],
        values=tuple(Price(v) for v in out),
        symbol=src.symbol,
        timeframe=src.timeframe,
        availability_mask=tuple(True for _ in out),
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
    if not close_series or len(close_series) <= 1 or len(close_series) < period + 1:
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
    # For losses, we need absolute values (negative_values returns negative numbers, we need positive)
    losses_raw = negative_values(SeriesContext(close=price_changes))
    # Convert losses to absolute values for RSI calculation
    # losses_raw has negative values or 0, we need positive values (absolute)
    losses_values = tuple(Price(-Decimal(str(v))) if Decimal(str(v)) < 0 else Price(0) for v in losses_raw.values)
    losses = CoreSeries[Price](
        timestamps=losses_raw.timestamps,
        values=losses_values,
        symbol=losses_raw.symbol,
        timeframe=losses_raw.timeframe,
        availability_mask=losses_raw.availability_mask
        if hasattr(losses_raw, "availability_mask")
        else tuple(True for _ in losses_values),
    )

    # Apply Wilder's Smoothing to gains and losses
    # Note: gains and losses are already shifted by 1 (from diff), so we need period+1
    # total values to get period smoothed values
    if len(gains) < period or len(losses) < period:
        return close_series.__class__(
            timestamps=(),
            values=(),
            symbol=close_series.symbol,
            timeframe=close_series.timeframe,
        )

    avg_gains = _wilder_smoothing(gains, period)
    avg_losses = _wilder_smoothing(losses, period)

    # Align timestamps (they should already be aligned, but ensure they match)
    if len(avg_gains) != len(avg_losses) or avg_gains.timestamps != avg_losses.timestamps:
        # Find common timestamps
        gain_ts_set = set(avg_gains.timestamps)
        loss_ts_set = set(avg_losses.timestamps)
        common_ts = sorted(gain_ts_set & loss_ts_set)

        if not common_ts:
            return close_series.__class__(
                timestamps=(),
                values=(),
                symbol=close_series.symbol,
                timeframe=close_series.timeframe,
            )

        # Build aligned series
        gain_map = {ts: val for ts, val in zip(avg_gains.timestamps, avg_gains.values, strict=False)}
        loss_map = {ts: val for ts, val in zip(avg_losses.timestamps, avg_losses.values, strict=False)}

        aligned_gains = [gain_map[ts] for ts in common_ts]
        aligned_losses = [loss_map[ts] for ts in common_ts]

        avg_gains = CoreSeries[Price](
            timestamps=tuple(common_ts),
            values=tuple(aligned_gains),
            symbol=avg_gains.symbol,
            timeframe=avg_gains.timeframe,
            availability_mask=tuple(True for _ in common_ts),
        )
        avg_losses = CoreSeries[Price](
            timestamps=tuple(common_ts),
            values=tuple(aligned_losses),
            symbol=avg_losses.symbol,
            timeframe=avg_losses.timeframe,
            availability_mask=tuple(True for _ in common_ts),
        )

    # Calculate RSI: 100 - (100 / (1 + RS))
    # RS = avg_gains / avg_losses (with epsilon to avoid division by zero)
    rsi_values: list[Price] = []
    epsilon = Decimal("1e-10")

    for gain, loss in zip(avg_gains.values, avg_losses.values, strict=False):
        gain_dec = Decimal(str(gain))
        loss_dec = Decimal(str(loss))

        # Avoid division by zero
        if loss_dec == 0:
            rs = gain_dec / epsilon
        else:
            rs = gain_dec / (loss_dec + epsilon)

        rsi_val = 100 - (100 / (1 + rs))
        # Clamp RSI to [0, 100] range
        rsi_val = max(Decimal(0), min(Decimal(100), rsi_val))
        rsi_values.append(Price(rsi_val))

    return CoreSeries[Price](
        timestamps=avg_gains.timestamps,
        values=tuple(rsi_values),
        symbol=avg_gains.symbol,
        timeframe=avg_gains.timeframe,
        availability_mask=tuple(True for _ in rsi_values),
    )
