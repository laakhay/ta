"""VWAP (Volume Weighted Average Price) indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class VWAPIndicator(BaseIndicator):
    """Volume Weighted Average Price.

    VWAP gives the average price a security has traded at throughout the day,
    based on both volume and price. It's calculated as:

        VWAP = Σ(Price × Volume) / Σ(Volume)

    Typically uses typical price (HLC3) = (High + Low + Close) / 3

    Uses:
        - Trading benchmark (institutional traders)
        - Support/resistance levels
        - Trend confirmation
        - Fair value reference

    Example:
        >>> result = VWAPIndicator.compute(input, price_field="hlc3")
        >>> btc_vwap = result.values["BTCUSDT"]  # [(timestamp, vwap_value), ...]
    """

    name: ClassVar[str] = "vwap"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare dependency on price and volume data.

        Returns:
            Requirements specifying need for complete OHLCV data.
        """
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field=None,  # Need full candle data (OHLCV)
                    window=WindowSpec(lookback_bars=200),
                    only_closed=True,
                )
            ]
        )

    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Compute VWAP series for each symbol.

        Can compute as:
        1. Cumulative VWAP (from start of data)
        2. Rolling VWAP (over a window)

        Args:
            input: TAInput with candles for each symbol
            **params:
                price_field (str, default="hlc3"): Price to use:
                    - "hlc3": Typical price (H+L+C)/3 [recommended]
                    - "close", "ohlc4", "hl2": Alternative prices
                window (int, optional): Rolling window size (bars)
                    - If None: Cumulative VWAP from start
                    - If set: Rolling VWAP over window

        Returns:
            TAOutput with VWAP series per symbol:
                {symbol: [(timestamp, vwap_value), ...]}

        Raises:
            ValueError: If invalid price_field or window
        """
        price_field = params.get("price_field", "hlc3")
        window = params.get("window", None)  # None = cumulative

        # Validate parameters
        if window is not None and window < 1:
            raise ValueError(f"VWAP window must be >= 1 or None, got {window}")

        valid_fields = {"open", "high", "low", "close", "hlc3", "ohlc4", "hl2"}
        if price_field not in valid_fields:
            raise ValueError(f"Invalid price_field '{price_field}'. Must be one of {valid_fields}")

        results = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])

            if not candles:
                continue

            # Extract price and volume series
            prices = []
            volumes = []

            for candle in candles:
                # Get price based on field
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

                volume = float(candle.volume)
                prices.append(price)
                volumes.append(volume)

            vwap_series = []

            if window is None:
                # Cumulative VWAP
                cum_pv = 0.0  # Cumulative price × volume
                cum_volume = 0.0  # Cumulative volume

                for i in range(len(candles)):
                    pv = prices[i] * volumes[i]
                    cum_pv += pv
                    cum_volume += volumes[i]

                    if cum_volume > 0:
                        vwap = cum_pv / cum_volume
                    else:
                        vwap = prices[i]

                    vwap_series.append((candles[i].timestamp, vwap))

            else:
                # Rolling VWAP
                for i in range(len(candles)):
                    # Get window [max(0, i-window+1) : i+1]
                    start_idx = max(0, i - window + 1)
                    window_prices = prices[start_idx : i + 1]
                    window_volumes = volumes[start_idx : i + 1]

                    # Calculate VWAP for window
                    pv_sum = sum(p * v for p, v in zip(window_prices, window_volumes, strict=True))
                    volume_sum = sum(window_volumes)

                    if volume_sum > 0:
                        vwap = pv_sum / volume_sum
                    else:
                        vwap = prices[i]

                    vwap_series.append((candles[i].timestamp, vwap))

            results[symbol] = vwap_series

        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={
                "price_field": price_field,
                "window": window if window else "cumulative",
                "series_length": len(results.get(input.scope_symbols[0], [])) if results else 0,
            },
        )


# Auto-register indicator
register(VWAPIndicator)
