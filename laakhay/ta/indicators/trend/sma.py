"""Simple Moving Average (SMA) indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec
from ...core.utils import slice_tail


class SMAIndicator(BaseIndicator):
    """Simple Moving Average.

    Computes the arithmetic mean of the last N closes for each symbol.
    This is a stateless, deterministic indicator - no internal state.
    """

    name: ClassVar[str] = "sma"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare dependency on price data (close field).

        Returns:
            Requirements specifying need for close prices with 200 bars lookback.
        """
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field="close",
                    window=WindowSpec(lookback_bars=200),  # Max reasonable SMA period
                    only_closed=True,
                )
            ]
        )

    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Compute SMA for each symbol in the input.

        Args:
            input: TAInput with candles for each symbol
            **params: period (int, default=20) - number of bars to average

        Returns:
            TAOutput with SMA values per symbol

        Raises:
            ValueError: If period < 1
        """
        period = params.get("period", 20)

        # Validate parameter
        if period < 1:
            raise ValueError(f"SMA period must be >= 1, got {period}")

        results = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])

            # Skip if insufficient data
            if len(candles) < period:
                continue

            # Get last N candles
            recent = slice_tail(candles, period)

            # Compute simple average of closes
            closes = [float(c.close) for c in recent]
            sma_value = sum(closes) / len(closes)

            results[symbol] = sma_value

        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={"period": period, "lookback_used": period},
        )


# Auto-register indicator
register(SMAIndicator)
