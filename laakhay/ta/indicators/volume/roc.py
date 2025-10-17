"""Volume Rate of Change (VROC) indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class VolumeROCIndicator(BaseIndicator):
    """Volume Rate of Change.

    Measures the percentage change in volume compared to N periods ago.
    Highlights surges or drops in activity relative to a moving baseline.

    Example:
        >>> result = VolumeROCIndicator.compute(input, period=14)
        >>> vroc_series = result.values["BTCUSDT"]
        >>> latest_vroc = vroc_series[-1][1]  # Percent change vs 14 bars ago
    """

    name: ClassVar[str] = "volume_roc"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Request OHLCV candles (volume field lives with price data)."""
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
        """Compute volume rate of change for each symbol.

        Args:
            input: TAInput containing candle data.
            **params:
                period (int, default=14): Lookback distance for comparison.
                multiplier (float, default=100.0): Scale factor for output.
                    Set to 100 for percentage change or 1 for decimal.

        Returns:
            TAOutput mapping symbols to (timestamp, roc_value) pairs.

        Raises:
            ValueError: If period < 1 or multiplier <= 0.
        """
        period = params.get("period", 14)
        multiplier = params.get("multiplier", 100.0)

        if period < 1:
            raise ValueError(f"VolumeROC period must be >= 1, got {period}")
        if multiplier <= 0:
            raise ValueError(f"VolumeROC multiplier must be > 0, got {multiplier}")

        results: dict[str, list[tuple]] = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])
            if len(candles) <= period:
                continue

            volumes = [float(c.volume) for c in candles]
            series: list[tuple] = []

            for i in range(period, len(candles)):
                previous_volume = volumes[i - period]
                current_volume = volumes[i]

                if previous_volume == 0:
                    roc_value = 0.0
                else:
                    roc_value = ((current_volume - previous_volume) / previous_volume) * multiplier

                timestamp = candles[i].timestamp
                series.append((timestamp, roc_value))

            results[symbol] = series

        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={
                "period": period,
                "multiplier": multiplier,
                "series_length": len(results.get(input.scope_symbols[0], [])) if results else 0,
            },
        )


# Auto-register indicator
register(VolumeROCIndicator)
