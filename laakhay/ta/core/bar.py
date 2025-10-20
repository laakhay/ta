"""Bar (OHLCV) data model"""

from dataclasses import dataclass
from typing import override, Any

from .types import Price, Qty, Timestamp, PriceLike, QtyLike, TimestampLike
from .coercers import coerce_price, coerce_qty
from .timestamps import coerce_timestamp

@dataclass(slots=True, frozen=True)
class Bar:
    """
    OHLCV bar data - immutable representation of a price bar.

    This is the fundamental data structure for technical analysis.
    Designed to be data-source agnostic - any provider can produce Bar instances.

    Attributes:
        ts: Timestamp (timezone-aware datetime)
        open: Opening price
        high: Highest price
        low: Lowest price
        close: Closing price
        volume: Trading volume
        is_closed: Whether the bar is closed/finalized
    """

    ts: Timestamp
    open: Price
    high: Price
    low: Price
    close: Price
    volume: Qty
    is_closed: bool = True

    def __post_init__(self):
        """Basic validation."""
        if self.high < self.low:
            raise ValueError("High must be >= low")
        if self.high < max(self.open, self.close):
            raise ValueError("High must be >= open and close")
        if self.low > min(self.open, self.close):
            raise ValueError("Low must be <= open and close")
        if self.volume < 0:
            raise ValueError("Volume must be >= 0")
    
    @property
    def hlc3(self) -> Price:
        """High + Low + Close / 3 (typical price)."""
        return (self.high + self.low + self.close) / 3
    
    @property
    def ohlc4(self) -> Price:
        """Open + High + Low + Close / 4 (average price)."""
        return (self.open + self.high + self.low + self.close) / 4
    
    @property
    def hl2(self) -> Price:
        """High + Low / 2 (mid price)."""
        return (self.high + self.low) / 2
    
    @property
    def body_size(self) -> Qty:
        """|Close - Open| (absolute body size)."""
        return abs(self.close - self.open)
    
    @property
    def upper_wick(self) -> Qty:
        """High - max(Open, Close) (upper wick)."""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_wick(self) -> Qty:
        """min(Open, Close) - Low (lower wick)."""
        return min(self.open, self.close) - self.low
    
    @property
    def total_range(self) -> Qty:
        """High - Low (total range)."""
        return self.high - self.low
    
    @override
    def __repr__(self) -> str:
        """Concise string representation for debugging."""
        return (
            f"Bar(ts={self.ts.isoformat()}, "
            f"o={self.open}, h={self.high}, l={self.low}, c={self.close}, "
            f"vol={self.volume}, closed={self.is_closed})"
        )


    @classmethod
    def from_raw(cls, ts: TimestampLike, open: PriceLike, high: PriceLike, low: PriceLike, close: PriceLike, volume: QtyLike, is_closed: bool = True) -> "Bar":
        """Create a Bar from raw data."""
        return cls(
            ts=coerce_timestamp(ts),
            open=coerce_price(open),
            high=coerce_price(high),
            low=coerce_price(low),
            close=coerce_price(close),
            volume=coerce_qty(volume),
            is_closed=is_closed,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Bar":
        """Create a Bar from a dictionary."""
        return cls(
            ts=coerce_timestamp(data.get("ts") or data.get("timestamp")),
            open=coerce_price(data.get("open") or data.get("open_price") or data.get("o")),
            high=coerce_price(data.get("high") or data.get("high_price") or data.get("h")),
            low=coerce_price(data.get("low") or data.get("low_price") or data.get("l")),
            close=coerce_price(data.get("close") or data.get("close_price") or data.get("c")),
            volume=coerce_qty(data.get("volume") or data.get("volume_qty") or data.get("v")),
            is_closed=data.get("is_closed", True) or data.get("closed", True) or data.get("x", True),
        )
