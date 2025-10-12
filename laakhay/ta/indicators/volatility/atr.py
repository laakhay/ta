"""ATR (Average True Range) indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class ATRIndicator(BaseIndicator):
    """Average True Range.

    ATR measures market volatility by decomposing the entire range of price
    movement for a given period. It's the average of True Range over a period.

    True Range is the greatest of:
        1. Current High - Current Low
        2. |Current High - Previous Close|
        3. |Current Low - Previous Close|

    Uses Wilder's smoothing (same as RSI):
        - First ATR = SMA of first 'period' TR values
        - Subsequent: ATR = (prev_ATR * (period-1) + current_TR) / period

    Uses:
        - Volatility measurement
        - Position sizing (risk management)
        - Stop-loss placement
        - Breakout confirmation

    Example:
        >>> result = ATRIndicator.compute(input, period=14)
        >>> btc_atr = result.values["BTCUSDT"]  # [(timestamp, atr_value), ...]
    """

    name: ClassVar[str] = "atr"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare dependency on OHLC data.

        Returns:
            Requirements specifying need for complete OHLC data.
        """
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field=None,  # Need full OHLC
                    window=WindowSpec(lookback_bars=200),
                    only_closed=True,
                )
            ]
        )

    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Compute ATR series for each symbol.

        Algorithm (Wilder's smoothing):
            1. Calculate True Range for each bar
            2. First ATR = SMA of first 'period' TR values
            3. For subsequent bars: ATR = (prev_ATR * (period-1) + current_TR) / period

        Args:
            input: TAInput with candles for each symbol
            **params:
                period (int, default=14): Lookback period for ATR

        Returns:
            TAOutput with ATR series per symbol:
                {symbol: [(timestamp, atr_value), ...]}

        Raises:
            ValueError: If period < 1
        """
        period = params.get("period", 14)

        # Validate parameters
        if period < 1:
            raise ValueError(f"ATR period must be >= 1, got {period}")

        results = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])

            # Need at least period+1 candles (1 for prev close + period for first ATR)
            if len(candles) < period + 1:
                continue

            # Calculate True Range for each bar
            true_ranges = []

            for i in range(1, len(candles)):
                current = candles[i]
                previous = candles[i - 1]

                high = float(current.high)
                low = float(current.low)
                prev_close = float(previous.close)

                # True Range = max of three ranges
                tr1 = high - low  # Current range
                tr2 = abs(high - prev_close)  # High to prev close
                tr3 = abs(low - prev_close)  # Low to prev close

                true_range = max(tr1, tr2, tr3)
                true_ranges.append(true_range)

            atr_series = []

            # Initialize with SMA of first 'period' TR values
            first_atr = sum(true_ranges[:period]) / period
            atr_series.append((candles[period].timestamp, first_atr))
            prev_atr = first_atr

            # Apply Wilder's smoothing for remaining values
            for i in range(period, len(true_ranges)):
                atr = (prev_atr * (period - 1) + true_ranges[i]) / period
                atr_series.append((candles[i + 1].timestamp, atr))
                prev_atr = atr

            results[symbol] = atr_series

        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={
                "period": period,
                "series_length": len(results.get(input.scope_symbols[0], [])) if results else 0,
            },
        )


# Auto-register indicator
register(ATRIndicator)
