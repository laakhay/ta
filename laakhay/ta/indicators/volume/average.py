"""Simple Volume Average indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class SimpleVolumeAverageIndicator(BaseIndicator):
    """Simple Volume Average (Volume SMA).

    Calculates the arithmetic mean of traded volume over a rolling window.
    Useful for identifying changes in participation by comparing current volume
    against its recent baseline.

    Example:
        >>> result = SimpleVolumeAverageIndicator.compute(input, period=20)
        >>> avg_volume_series = result.values["BTCUSDT"]
        >>> latest_avg_volume = avg_volume_series[-1][1]
    """

    name: ClassVar[str] = "volume_sma"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Request OHLCV candles (volume is part of price data)."""
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field=None,
                    window=WindowSpec(lookback_bars=200),
                    only_closed=True,
                )
            ]
        )

    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Compute rolling average volume for each symbol.

        Args:
            input: TAInput holding candle data for the requested symbols.
            **params:
                period (int, default=20): Number of bars to average.

        Returns:
            TAOutput mapping symbols to time series of (timestamp, avg_volume).

        Raises:
            ValueError: If period < 1.
        """
        period = params.get("period", 20)

        if period < 1:
            raise ValueError(f"SimpleVolumeAverage period must be >= 1, got {period}")

        results: dict[str, list[tuple]] = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])
            if len(candles) < period:
                continue

            volumes = [float(c.volume) for c in candles]
            series: list[tuple] = []

            # Initialize rolling sum with first window.
            window_sum = sum(volumes[:period])

            for i in range(period - 1, len(candles)):
                if i >= period:
                    window_sum += volumes[i] - volumes[i - period]

                avg_volume = window_sum / period
                timestamp = candles[i].timestamp
                series.append((timestamp, avg_volume))

            results[symbol] = series

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
register(SimpleVolumeAverageIndicator)
