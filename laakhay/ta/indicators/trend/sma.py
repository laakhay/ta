"""Simple Moving Average (SMA) indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class SMAIndicator(BaseIndicator):
    """Simple Moving Average.

    Computes the arithmetic mean of prices over a rolling window.
    Returns a time series of SMA values for efficient backtesting and analysis.

    For 100 candles with period=20, returns ~80 SMA values (one per valid window).
    This is a stateless, deterministic indicator - no internal state.

    Example:
        >>> # Get SMA series for backtesting
        >>> result = SMAIndicator.compute(input, period=20, price_field="close")
        >>> btc_sma = result.values["BTCUSDT"]  # List of (timestamp, sma_value)
        >>> print(f"Got {len(btc_sma)} SMA values")  # ~80 for 100 candles
    """

    name: ClassVar[str] = "sma"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare dependency on price data.

        Supports any price field via params, so we request generic price data
        with max reasonable lookback (200 bars for typical SMA usage).

        Returns:
            Requirements specifying need for price data with 200 bars lookback.
        """
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field=None,  # Caller specifies via params
                    window=WindowSpec(lookback_bars=200),  # Max reasonable SMA period
                    only_closed=True,
                )
            ]
        )

    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Compute SMA series for each symbol.

        Returns a time series of SMA values - one for each valid window.
        For example, 100 candles with period=20 yields ~80 SMA values.

        Args:
            input: TAInput with candles for each symbol
            **params:
                period (int, default=20): Number of bars to average
                price_field (str, default="close"): Price to use:
                    - "open", "high", "low", "close": OHLC fields
                    - "hlc3": Typical price (H+L+C)/3
                    - "ohlc4": Average price (O+H+L+C)/4
                    - "hl2": Median price (H+L)/2

        Returns:
            TAOutput with SMA series per symbol:
                {symbol: [(timestamp, sma_value), (timestamp, sma_value), ...]}

        Raises:
            ValueError: If period < 1 or invalid price_field
        """
        period = params.get("period", 20)
        price_field = params.get("price_field", "close")

        # Validate parameters
        if period < 1:
            raise ValueError(f"SMA period must be >= 1, got {period}")

        valid_fields = {"open", "high", "low", "close", "hlc3", "ohlc4", "hl2"}
        if price_field not in valid_fields:
            raise ValueError(
                f"Invalid price_field '{price_field}'. Must be one of {valid_fields}"
            )

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

            # Compute SMA for all valid windows
            # For 100 candles with period=20: indices 19-99 are valid (80 values)
            sma_series = []
            for i in range(period - 1, len(candles)):
                # Get window of prices: [i-period+1 : i+1]
                window_prices = prices[i - period + 1 : i + 1]
                sma_value = sum(window_prices) / period
                timestamp = candles[i].timestamp
                sma_series.append((timestamp, sma_value))

            results[symbol] = sma_series

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
register(SMAIndicator)
