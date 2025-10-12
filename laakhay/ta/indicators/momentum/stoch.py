"""Stochastic Oscillator indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class StochasticIndicator(BaseIndicator):
    """Stochastic Oscillator.

    The Stochastic Oscillator compares a security's closing price to its price
    range over a given time period. It consists of two lines:

        %K (Fast): (Close - Lowest Low) / (Highest High - Lowest Low) × 100
        %D (Slow): SMA of %K over signal_period

    Standard settings: k_period=14, d_period=3

    The oscillator ranges from 0 to 100:
        - Above 80: Potentially overbought
        - Below 20: Potentially oversold
        - Crossovers: %K crossing %D generates signals

    Uses:
        - Overbought/oversold identification
        - Divergence detection
        - Momentum confirmation
        - Crossover signals

    Example:
        >>> result = StochasticIndicator.compute(input, k_period=14, d_period=3)
        >>> btc_stoch = result.values["BTCUSDT"]
        >>> # Returns: {"k": [(ts, val), ...], "d": [(ts, val), ...]}
    """

    name: ClassVar[str] = "stoch"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare dependency on OHLC data.

        Returns:
            Requirements specifying need for High/Low/Close data.
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
        """Compute Stochastic Oscillator series for each symbol.

        Algorithm:
            1. For each bar, find highest high and lowest low over k_period
            2. %K = (Close - LL) / (HH - LL) × 100
            3. %D = SMA of %K over d_period

        Args:
            input: TAInput with candles for each symbol
            **params:
                k_period (int, default=14): Lookback for high/low range
                d_period (int, default=3): SMA period for %D signal line
                smooth_k (int, default=1): Additional smoothing for %K (1=no smoothing)

        Returns:
            TAOutput with Stochastic values per symbol:
                {symbol: {
                    "k": [(timestamp, k_value), ...],
                    "d": [(timestamp, d_value), ...]
                }}

        Raises:
            ValueError: If k_period < 1 or d_period < 1
        """
        k_period = params.get("k_period", 14)
        d_period = params.get("d_period", 3)
        smooth_k = params.get("smooth_k", 1)  # 1 = no smoothing (fast stochastic)

        # Validate parameters
        if k_period < 1:
            raise ValueError(f"k_period must be >= 1, got {k_period}")
        if d_period < 1:
            raise ValueError(f"d_period must be >= 1, got {d_period}")
        if smooth_k < 1:
            raise ValueError(f"smooth_k must be >= 1, got {smooth_k}")

        results = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])

            # Need at least k_period candles
            min_required = k_period + smooth_k - 1 + d_period - 1
            if len(candles) < min_required:
                continue

            # Extract high, low, close series
            highs = [float(c.high) for c in candles]
            lows = [float(c.low) for c in candles]
            closes = [float(c.close) for c in candles]

            # Calculate raw %K values
            raw_k_values = []

            for i in range(k_period - 1, len(candles)):
                # Find highest high and lowest low in window
                window_highs = highs[i - k_period + 1 : i + 1]
                window_lows = lows[i - k_period + 1 : i + 1]

                highest_high = max(window_highs)
                lowest_low = min(window_lows)

                # Calculate %K
                if highest_high == lowest_low:
                    # Avoid division by zero (flat period)
                    k_value = 50.0
                else:
                    k_value = ((closes[i] - lowest_low) / (highest_high - lowest_low)) * 100.0

                raw_k_values.append(k_value)

            # Apply smoothing to %K if smooth_k > 1
            if smooth_k > 1:
                k_values = []
                for i in range(smooth_k - 1, len(raw_k_values)):
                    window = raw_k_values[i - smooth_k + 1 : i + 1]
                    smoothed_k = sum(window) / smooth_k
                    k_values.append(smoothed_k)
                k_start_idx = k_period - 1 + smooth_k - 1
            else:
                k_values = raw_k_values
                k_start_idx = k_period - 1

            # Calculate %D (SMA of %K)
            d_values = []
            for i in range(d_period - 1, len(k_values)):
                window = k_values[i - d_period + 1 : i + 1]
                d_value = sum(window) / d_period
                d_values.append(d_value)

            # Build output series (aligned to %D start)
            k_series = []
            d_series = []

            d_start_idx = k_start_idx + d_period - 1

            for i in range(len(d_values)):
                k_idx = d_period - 1 + i
                timestamp = candles[d_start_idx + i].timestamp

                k_series.append((timestamp, k_values[k_idx]))
                d_series.append((timestamp, d_values[i]))

            results[symbol] = {
                "k": k_series,
                "d": d_series,
            }

        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={
                "k_period": k_period,
                "d_period": d_period,
                "smooth_k": smooth_k,
                "series_length": len(results[input.scope_symbols[0]]["k"]) if results else 0,
            },
        )


# Auto-register indicator
register(StochasticIndicator)
