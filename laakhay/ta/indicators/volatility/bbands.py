"""Bollinger Bands indicator."""

from __future__ import annotations

import math
from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class BollingerBandsIndicator(BaseIndicator):
    """Bollinger Bands.

    Bollinger Bands consist of three lines:
        - Middle Band: Simple Moving Average (SMA)
        - Upper Band: SMA + (std_dev * num_std)
        - Lower Band: SMA - (std_dev * num_std)

    Standard settings: period=20, num_std=2

    The bands expand during high volatility and contract during low volatility.

    Uses:
        - Volatility measurement
        - Overbought/oversold identification
        - Squeeze patterns (low volatility → breakout)
        - Mean reversion trading
        - Breakout trading

    Example:
        >>> result = BollingerBandsIndicator.compute(input, period=20, num_std=2)
        >>> btc_bb = result.values["BTCUSDT"]
        >>> # Returns: {"upper": [(ts, val), ...], "middle": [...], "lower": [...]}
    """

    name: ClassVar[str] = "bbands"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare dependency on price data.

        Returns:
            Requirements specifying need for price data.
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
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Compute Bollinger Bands series for each symbol.

        Algorithm:
            1. Calculate SMA (middle band)
            2. Calculate standard deviation for each window
            3. Upper = SMA + (std_dev * num_std)
            4. Lower = SMA - (std_dev * num_std)

        Args:
            input: TAInput with candles for each symbol
            **params:
                period (int, default=20): Lookback period for SMA and std dev
                num_std (float, default=2.0): Number of standard deviations
                price_field (str, default="close"): Price to use

        Returns:
            TAOutput with Bollinger Bands per symbol:
                {symbol: {
                    "upper": [(timestamp, value), ...],
                    "middle": [(timestamp, value), ...],
                    "lower": [(timestamp, value), ...]
                }}

        Raises:
            ValueError: If period < 2 or num_std <= 0
        """
        period = params.get("period", 20)
        num_std = params.get("num_std", 2.0)
        price_field = params.get("price_field", "close")

        # Validate parameters
        if period < 2:
            raise ValueError(f"Bollinger Bands period must be >= 2, got {period}")
        if num_std <= 0:
            raise ValueError(f"num_std must be > 0, got {num_std}")

        valid_fields = {"open", "high", "low", "close", "hlc3", "ohlc4", "hl2"}
        if price_field not in valid_fields:
            raise ValueError(
                f"Invalid price_field '{price_field}'. Must be one of {valid_fields}"
            )

        results = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])

            # Need at least period candles
            if len(candles) < period:
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

            upper_band = []
            middle_band = []
            lower_band = []

            # Calculate bands for each window
            for i in range(period - 1, len(candles)):
                # Get window of prices
                window_prices = prices[i - period + 1 : i + 1]

                # Calculate SMA (middle band)
                sma = sum(window_prices) / period

                # Calculate standard deviation
                variance = sum((p - sma) ** 2 for p in window_prices) / period
                std_dev = math.sqrt(variance)

                # Calculate upper and lower bands
                upper = sma + (std_dev * num_std)
                lower = sma - (std_dev * num_std)

                timestamp = candles[i].timestamp
                upper_band.append((timestamp, upper))
                middle_band.append((timestamp, sma))
                lower_band.append((timestamp, lower))

            results[symbol] = {
                "upper": upper_band,
                "middle": middle_band,
                "lower": lower_band,
            }

        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={
                "period": period,
                "num_std": num_std,
                "price_field": price_field,
                "series_length": len(results[input.scope_symbols[0]]["middle"]) if results else 0,
            },
        )


# Auto-register indicator
register(BollingerBandsIndicator)
