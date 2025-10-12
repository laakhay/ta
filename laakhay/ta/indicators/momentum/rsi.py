"""Relative Strength Index (RSI) indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class RSIIndicator(BaseIndicator):
    """Relative Strength Index.

    Measures the magnitude of recent price changes to evaluate
    overbought or oversold conditions in the price of an asset.

    Formula:
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss

    Uses Wilder's smoothing (modified EMA):
        - First avg gain/loss = SMA of gains/losses
        - Subsequent = (prev_avg * (period-1) + current) / period

    RSI oscillates between 0-100:
        - Above 70: Potentially overbought
        - Below 30: Potentially oversold

    Example:
        >>> result = RSIIndicator.compute(input, period=14)
        >>> btc_rsi = result.values["BTCUSDT"]  # [(timestamp, rsi_value), ...]
    """

    name: ClassVar[str] = "rsi"
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
        """Compute RSI series for each symbol.

        Algorithm (Wilder's smoothing):
            1. Calculate price changes (gains and losses)
            2. First avg gain/loss = SMA over first 'period' values
            3. For subsequent bars: avg = (prev_avg * (period-1) + current) / period
            4. RS = avg_gain / avg_loss
            5. RSI = 100 - (100 / (1 + RS))

        Args:
            input: TAInput with candles for each symbol
            **params:
                period (int, default=14): Lookback period for RSI
                price_field (str, default="close"): Price to use for calculations

        Returns:
            TAOutput with RSI series per symbol:
                {symbol: [(timestamp, rsi_value), ...]}
                RSI values range from 0 to 100

        Raises:
            ValueError: If period < 1 or invalid price_field
        """
        period = params.get("period", 14)
        price_field = params.get("price_field", "close")

        # Validate parameters
        if period < 2:
            raise ValueError(f"RSI period must be >= 2, got {period}")

        valid_fields = {"open", "high", "low", "close", "hlc3", "ohlc4", "hl2"}
        if price_field not in valid_fields:
            raise ValueError(
                f"Invalid price_field '{price_field}'. Must be one of {valid_fields}"
            )

        results = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])

            # Need at least period+1 candles (period for first avg + 1 for first RSI)
            if len(candles) < period + 1:
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

            # Calculate price changes
            changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

            # Separate gains and losses
            gains = [max(change, 0.0) for change in changes]
            losses = [abs(min(change, 0.0)) for change in changes]

            # Initialize with SMA of first 'period' values
            avg_gain = sum(gains[:period]) / period
            avg_loss = sum(losses[:period]) / period

            rsi_series = []

            # First RSI value (at index period, which is period+1 candles)
            if avg_loss == 0:
                rsi = 100.0 if avg_gain > 0 else 50.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100.0 - (100.0 / (1.0 + rs))
            rsi_series.append((candles[period].timestamp, rsi))

            # Apply Wilder's smoothing for remaining values
            for i in range(period, len(changes)):
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period

                if avg_loss == 0:
                    rsi = 100.0 if avg_gain > 0 else 50.0
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100.0 - (100.0 / (1.0 + rs))

                rsi_series.append((candles[i + 1].timestamp, rsi))

            results[symbol] = rsi_series

        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={
                "period": period,
                "price_field": price_field,
                "series_length": len(results.get(input.scope_symbols[0], [])) if results else 0,
            },
        )


# Auto-register indicator
register(RSIIndicator)
