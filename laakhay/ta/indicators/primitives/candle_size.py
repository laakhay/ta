"""Candle size calculation indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class CandleSizeIndicator(BaseIndicator):
    """Calculate candle size metrics.

    Provides various candle size calculations for technical analysis:
    - open_close: Absolute difference between open and close prices
    - high_low: Absolute difference between high and low prices
    - body_size: Size of the candle body (open to close)
    - wick_size: Size of the candle wicks (high/low to body)

    This is a stateless, deterministic indicator - no internal state.

    Example:
        >>> # Get candle size series
        >>> result = CandleSizeIndicator.compute(input, size_type="open_close")
        >>> btc_sizes = result.values["BTCUSDT"]  # List of (timestamp, size_value)
        >>> print(f"Got {len(btc_sizes)} candle size values")
    """

    name: ClassVar[str] = "candle_size"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare dependency on price data.

        Returns:
            Requirements specifying need for price data with minimal lookback.
        """
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field=None,
                    window=WindowSpec(lookback_bars=1),
                    only_closed=True,
                )
            ]
        )

    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Compute candle size series for each symbol.

        Args:
            input: TAInput with candles for each symbol
            **params:
                size_type (str, default="open_close"): Type of size calculation:
                    - "open_close": |close - open| (candle body size)
                    - "high_low": |high - low| (total candle range)
                    - "body_size": |close - open| (same as open_close)
                    - "upper_wick": |high - max(open, close)| (upper wick size)
                    - "lower_wick": |min(open, close) - low| (lower wick size)
                    - "total_wick": upper_wick + lower_wick (total wick size)

        Returns:
            TAOutput with candle size series per symbol:
                {symbol: [(timestamp, size_value), (timestamp, size_value), ...]}

        Raises:
            ValueError: If size_type is invalid
        """
        size_type = params.get("size_type", "open_close")

        # Validate size_type parameter
        valid_types = {
            "open_close",
            "high_low",
            "body_size",
            "upper_wick",
            "lower_wick",
            "total_wick",
        }
        if size_type not in valid_types:
            raise ValueError(f"Invalid size_type '{size_type}'. Must be one of {valid_types}")

        results = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])
            if not candles:
                continue

            # Calculate size series
            size_series = []
            for candle in candles:
                open_price = float(candle.open)
                high_price = float(candle.high)
                low_price = float(candle.low)
                close_price = float(candle.close)

                if size_type == "open_close" or size_type == "body_size":
                    size_value = abs(close_price - open_price)
                elif size_type == "high_low":
                    size_value = abs(high_price - low_price)
                elif size_type == "upper_wick":
                    body_top = max(open_price, close_price)
                    size_value = abs(high_price - body_top)
                elif size_type == "lower_wick":
                    body_bottom = min(open_price, close_price)
                    size_value = abs(body_bottom - low_price)
                elif size_type == "total_wick":
                    body_top = max(open_price, close_price)
                    body_bottom = min(open_price, close_price)
                    upper_wick = abs(high_price - body_top)
                    lower_wick = abs(body_bottom - low_price)
                    size_value = upper_wick + lower_wick
                else:  # pragma: no cover - validated above
                    continue

                size_series.append((candle.timestamp, size_value))

            results[symbol] = size_series

        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={
                "size_type": size_type,
                "series_length": len(results.get(input.scope_symbols[0], [])) if results else 0,
            },
        )


# Auto-register indicator
register(CandleSizeIndicator)
