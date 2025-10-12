from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# What kinds of raw series an indicator may consume.
DataKind = Literal[
    "price",  # OHLCV (Candle)
    "volume",  # explicit volume dependency
    "oi",  # open interest
    "funding",  # funding rates
    "mark_price",  # mark/index price series
    "trades",  # tick/agg trades (future)
    "orderbook",  # L2/L3 diffs or snapshots (future)
]

# Optional price field selector when kind == "price"
PriceField = Literal["open", "high", "low", "close", "vwap", "hlc3", "ohlc4"]


class WindowSpec(BaseModel):
    """
    Expresses minimal historical context required at evaluation time.
    lookback_bars: number of historical *closed* bars needed.
    min_lag_bars: additional lag (e.g., require strictly previous close).
    """

    lookback_bars: int = Field(default=0, ge=0)
    min_lag_bars: int = Field(default=0, ge=0)


class RawDataRequirement(BaseModel):
    """
    A declaration of raw data needs.
    symbols=None means 'inherit from request scope'.
    """

    kind: DataKind
    price_field: PriceField | None = None
    symbols: list[str] | None = None
    window: WindowSpec = Field(default_factory=WindowSpec)
    only_closed: bool = True


class IndicatorRef(BaseModel):
    """
    A declaration for depending on another indicator's output.
    """

    name: str
    params: dict[str, Any] = Field(default_factory=dict)
    symbols: list[str] | None = None
    window: WindowSpec = Field(default_factory=WindowSpec)


class IndicatorRequirements(BaseModel):
    """
    Full set of dependencies for an indicator.
    """

    raw: list[RawDataRequirement] = Field(default_factory=list)
    indicators: list[IndicatorRef] = Field(default_factory=list)
