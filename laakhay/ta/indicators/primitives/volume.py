"""Volume accessor indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class VolumeIndicator(BaseIndicator):
    """Expose raw volume from candles as an indicator series.

    Provides access to volume data for use in other indicators or direct analysis.
    Returns a time series of volume values for efficient backtesting and analysis.

    This is a stateless, deterministic indicator - no internal state.

    Example:
        >>> # Get volume series for analysis
        >>> result = VolumeIndicator.compute(input)
        >>> btc_volume = result.values["BTCUSDT"]  # List of (timestamp, volume_value)
        >>> print(f"Got {len(btc_volume)} volume values")
    """

    name: ClassVar[str] = "volume"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare dependency on price data (which includes volume).

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
        """Compute volume series for each symbol.

        Args:
            input: TAInput with candles for each symbol
            **params: No parameters needed for basic volume access

        Returns:
            TAOutput with volume series per symbol:
                {symbol: [(timestamp, volume_value), (timestamp, volume_value), ...]}

        Raises:
            ValueError: If invalid parameters are provided
        """
        # Validate parameters (no parameters expected for basic volume)
        if params:
            raise ValueError("VolumeIndicator does not accept parameters")

        results = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])
            if not candles:
                continue

            # Extract volume series
            volume_series = []
            for candle in candles:
                volume_value = float(candle.volume)
                volume_series.append((candle.timestamp, volume_value))

            results[symbol] = volume_series

        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={"series_length": len(results.get(input.scope_symbols[0], [])) if results else 0},
        )


# Auto-register indicator
register(VolumeIndicator)
