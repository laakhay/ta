"""MACD (Moving Average Convergence Divergence) indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class MACDIndicator(BaseIndicator):
    """Moving Average Convergence Divergence.

    MACD is a trend-following momentum indicator that shows the relationship
    between two moving averages of a security's price.

    Components:
        - MACD Line = EMA(fast_period) - EMA(slow_period)
        - Signal Line = EMA(signal_period) of MACD Line
        - Histogram = MACD Line - Signal Line

    Standard settings: fast=12, slow=26, signal=9

    Interpretation:
        - MACD above signal: Bullish momentum
        - MACD below signal: Bearish momentum
        - Histogram growing: Momentum accelerating
        - Histogram shrinking: Momentum decelerating

    Example:
        >>> result = MACDIndicator.compute(input, fast=12, slow=26, signal=9)
        >>> btc_macd = result.values["BTCUSDT"]
        >>> # Returns: {"macd": [(ts, val), ...], "signal": [...], "histogram": [...]}
    """

    name: ClassVar[str] = "macd"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare dependency on price data.

        Returns:
            Requirements specifying need for price data with 200 bars lookback.
        """
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field=None,  # Caller specifies via params
                    window=WindowSpec(lookback_bars=200),
                    only_closed=True,
                )
            ]
        )

    @classmethod
    def _compute_ema(cls, prices: list[float], period: int) -> list[float]:
        """Compute EMA helper method.

        Uses SMA for initialization, then applies EMA formula.
        """
        if len(prices) < period:
            return []

        alpha = 2.0 / (period + 1)
        ema_values = []

        # Initialize with SMA
        initial_sma = sum(prices[:period]) / period
        ema_values.append(initial_sma)
        prev_ema = initial_sma

        # Apply EMA formula
        for i in range(period, len(prices)):
            ema = prices[i] * alpha + prev_ema * (1 - alpha)
            ema_values.append(ema)
            prev_ema = ema

        return ema_values

    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Compute MACD series for each symbol.

        Algorithm:
            1. Compute fast EMA (default 12)
            2. Compute slow EMA (default 26)
            3. MACD = fast_EMA - slow_EMA (starting from slow_period bar)
            4. Signal = EMA(signal_period) of MACD line
            5. Histogram = MACD - Signal

        Args:
            input: TAInput with candles for each symbol
            **params:
                fast (int, default=12): Fast EMA period
                slow (int, default=26): Slow EMA period
                signal (int, default=9): Signal line EMA period
                price_field (str, default="close"): Price to use

        Returns:
            TAOutput with MACD components per symbol:
                {symbol: {
                    "macd": [(timestamp, macd_value), ...],
                    "signal": [(timestamp, signal_value), ...],
                    "histogram": [(timestamp, histogram_value), ...]
                }}

        Raises:
            ValueError: If slow <= fast or invalid parameters
        """
        fast_period = params.get("fast", 12)
        slow_period = params.get("slow", 26)
        signal_period = params.get("signal", 9)
        price_field = params.get("price_field", "close")

        # Validate parameters
        if slow_period <= fast_period:
            raise ValueError(
                f"Slow period ({slow_period}) must be > fast period ({fast_period})"
            )
        if fast_period < 2:
            raise ValueError(f"Fast period must be >= 2, got {fast_period}")
        if signal_period < 1:
            raise ValueError(f"Signal period must be >= 1, got {signal_period}")

        valid_fields = {"open", "high", "low", "close", "hlc3", "ohlc4", "hl2"}
        if price_field not in valid_fields:
            raise ValueError(
                f"Invalid price_field '{price_field}'. Must be one of {valid_fields}"
            )

        results = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])

            # Need enough data for slow EMA + signal EMA
            min_required = slow_period + signal_period
            if len(candles) < min_required:
                continue

            # Extract price series
            prices = []
            for candle in candles:
                if price_field == "open":
                    price = float(candle.open)
                elif price_field == "high":
                    price = float(candle.high)
                elif price_field == "low":
                    price = float(candle.low)
                elif price_field == "close":
                    price = float(candle.close)
                elif price_field == "hlc3":
                    price = float(candle.hlc3)
                elif price_field == "ohlc4":
                    price = float(candle.ohlc4)
                elif price_field == "hl2":
                    price = float(candle.hl2)
                prices.append(price)

            # Compute fast and slow EMAs
            fast_ema = cls._compute_ema(prices, fast_period)
            slow_ema = cls._compute_ema(prices, slow_period)

            # MACD line = fast_EMA - slow_EMA
            # Start from slow_period-1 (first slow EMA) and align with fast EMA
            macd_values = []
            macd_timestamps = []
            offset = slow_period - fast_period  # How many more bars slow needs

            for i in range(len(slow_ema)):
                macd = fast_ema[i + offset] - slow_ema[i]
                macd_values.append(macd)
                macd_timestamps.append(candles[slow_period - 1 + i].timestamp)

            # Signal line = EMA of MACD
            signal_ema = cls._compute_ema(macd_values, signal_period)

            # Build output series (aligned to signal line start)
            macd_series = []
            signal_series = []
            histogram_series = []

            signal_start_idx = signal_period - 1
            for i in range(len(signal_ema)):
                idx = signal_start_idx + i
                timestamp = macd_timestamps[idx]
                macd_val = macd_values[idx]
                signal_val = signal_ema[i]
                histogram_val = macd_val - signal_val

                macd_series.append((timestamp, macd_val))
                signal_series.append((timestamp, signal_val))
                histogram_series.append((timestamp, histogram_val))

            results[symbol] = {
                "macd": macd_series,
                "signal": signal_series,
                "histogram": histogram_series,
            }

        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={
                "fast": fast_period,
                "slow": slow_period,
                "signal": signal_period,
                "price_field": price_field,
                "series_length": len(results[input.scope_symbols[0]]["macd"]) if results else 0,
            },
        )


# Auto-register indicator
register(MACDIndicator)
