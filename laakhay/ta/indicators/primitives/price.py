"""Simple price accessor indicator."""

from __future__ import annotations

from typing import ClassVar, Literal

from ...core import BaseIndicator, TAInput, TAOutput
from ...core.registry import register
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec


class PriceIndicator(BaseIndicator):
    """Expose raw price fields from candles as an indicator series."""

    name: ClassVar[str] = "price"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field=None,
                    window=WindowSpec(lookback_bars=2),
                    only_closed=True,
                )
            ]
        )

    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        price_field = params.get("price_field", "close")
        valid_fields = {"open", "high", "low", "close", "hl2", "hlc3", "ohlc4"}
        if price_field not in valid_fields:
            raise ValueError(
                f"Unsupported price_field '{price_field}'. Must be one of {valid_fields}"
            )

        values = {}

        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])
            if not candles:
                continue

            series = []
            for candle in candles:
                if price_field == "open":
                    value = float(candle.open)
                elif price_field == "high":
                    value = float(candle.high)
                elif price_field == "low":
                    value = float(candle.low)
                elif price_field == "close":
                    value = float(candle.close)
                elif price_field == "hl2":
                    value = float(candle.hl2)
                elif price_field == "hlc3":
                    value = float(candle.hlc3)
                elif price_field == "ohlc4":
                    value = float(candle.ohlc4)
                else:  # pragma: no cover - validated above
                    continue
                series.append((candle.timestamp, value))

            values[symbol] = series

        return TAOutput(
            name=cls.name, values=values, ts=input.eval_ts, meta={"price_field": price_field}
        )


register(PriceIndicator)
