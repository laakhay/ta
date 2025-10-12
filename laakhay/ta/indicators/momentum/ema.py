"""Exponential Moving Average (EMA) indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class EMAIndicator(BaseIndicator):
    """Exponential Moving Average.

    Computes the exponential moving average using the standard formula:
        EMA(t) = price(t) * α + EMA(t-1) * (1 - α)
        where α = 2 / (period + 1)

    Uses SMA for initial value (first period bars), then applies EMA formula.
    Returns a time series of EMA values for efficient backtesting and analysis.

    Example:
        >>> # Get EMA series for backtesting
        >>> result = EMAIndicator.compute(input, period=20, price_field="close")
        >>> btc_ema = result.values["BTCUSDT"]  # List of (timestamp, ema_value)
        >>> print(f"Got {len(btc_ema)} EMA values")
    """

    name: ClassVar[str] = "ema"
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
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Compute EMA series for each symbol.

        Returns a time series of EMA values - one for each bar starting from period.
        Uses SMA of first period bars as the initial EMA value.

        Args:
            input: TAInput with candles for each symbol
            **params:
                period (int, default=20): Number of bars for EMA calculation
                price_field (str, default="close"): Price to use:
                    - "open", "high", "low", "close": OHLC fields
                    - "hlc3": Typical price (H+L+C)/3
                    - "ohlc4": Average price (O+H+L+C)/4
                    - "hl2": Median price (H+L)/2

        Returns:
            TAOutput with EMA series per symbol:
                {symbol: [(timestamp, ema_value), ...]}

        Raises:
            ValueError: If period < 1 or invalid price_field

        Algorithm:
            1. Calculate SMA of first 'period' bars as initial EMA
            2. For each subsequent bar: EMA = price * α + prev_EMA * (1 - α)
            3. α (smoothing factor) = 2 / (period + 1)
        """
        period = params.get("period", 20)
        price_field = params.get("price_field", "close")

        # Validate parameters
        if period < 1:
            raise ValueError(f"EMA period must be >= 1, got {period}")

        valid_fields = {"open", "high", "low", "close", "hlc3", "ohlc4", "hl2"}
        if price_field not in valid_fields:
            raise ValueError(
                f"Invalid price_field '{price_field}'. Must be one of {valid_fields}"
            )

        # Calculate smoothing factor (alpha)
        alpha = 2.0 / (period + 1)

        results = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])

            # Skip if insufficient data
            if len(candles) < period:
                continue

            # Extract price series based on price_field
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

            ema_series = []

            # Step 1: Initialize with SMA of first 'period' bars
            initial_sma = sum(prices[:period]) / period
            ema_value = initial_sma
            ema_series.append((candles[period - 1].timestamp, ema_value))

            # Step 2: Apply EMA formula for remaining bars
            for i in range(period, len(candles)):
                ema_value = prices[i] * alpha + ema_value * (1 - alpha)
                ema_series.append((candles[i].timestamp, ema_value))

            results[symbol] = ema_series

        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={
                "period": period,
                "price_field": price_field,
                "alpha": alpha,
                "series_length": len(results.get(input.scope_symbols[0], [])) if results else 0,
            },
        )


# Auto-register indicator
register(EMAIndicator)
