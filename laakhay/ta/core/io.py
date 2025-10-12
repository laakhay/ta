"""Input/Output data structures for the TA engine.

This module defines the contracts for indicator inputs and outputs,
making the engine data-source agnostic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from ..models import Candle


# Legacy point types for lightweight time-series data
# Use full models (FundingRate, OpenInterest, MarkPrice) when richer metadata is needed
class OIPoint(BaseModel):
    """Lightweight open interest data point."""
    ts: datetime
    oi: Decimal


class FundingPoint(BaseModel):
    """Lightweight funding rate data point."""
    ts: datetime
    rate: Decimal


class MarkPricePoint(BaseModel):
    """Lightweight mark price data point."""
    ts: datetime
    price: Decimal


class TAInput(BaseModel):
    """
    Engine-provided input bundle for a single-timeframe, multi-asset evaluation.
    
    This is what indicators receive as input. Keys are plain symbols (e.g., "BTCUSDT").
    Data sources must provide data in this format to use laakhay-ta.
    """
    candles: Mapping[str, Sequence[Candle]]

    # Optional raw series per symbol
    oi: Mapping[str, Sequence[OIPoint]] | None = None
    funding: Mapping[str, Sequence[FundingPoint]] | None = None
    mark_price: Mapping[str, Sequence[MarkPricePoint]] | None = None

    # Injected upstream indicator outputs (for composition)
    # Key: (indicator_name, params_hash, symbol) -> value/series (indicator-defined)
    indicators: Mapping[tuple[str, str, str], Any] | None = None

    # Evaluation scope
    scope_symbols: Sequence[str]

    # Evaluation timestamp (e.g., last closed bar). Optional for batch backfills.
    eval_ts: datetime | None = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class TAOutput(BaseModel):
    """
    Per-symbol indicator outputs and associated metadata.
    
    This is what indicators return after computation.
    """
    name: str
    values: Mapping[str, Any]           # symbol -> scalar / vector / dict
    ts: datetime | None = None          # common eval time (optional)
    meta: dict[str, Any] = {}           # e.g., {"lookback_used": 200, "notes": "..."}
