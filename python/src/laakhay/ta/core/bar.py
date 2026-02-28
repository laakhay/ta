"""Bar (OHLCV) data model"""

from dataclasses import dataclass
from typing import Any, override

from .coercers import coerce_price, coerce_qty
from .timestamps import coerce_timestamp
from .types import Price, PriceLike, Qty, QtyLike, Timestamp, TimestampLike


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
    def from_raw(
        cls,
        ts: TimestampLike,
        open: PriceLike,
        high: PriceLike,
        low: PriceLike,
        close: PriceLike,
        volume: QtyLike,
        is_closed: bool = True,
    ) -> "Bar":
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

        def require(field: str, aliases: list[str]) -> Any:
            for alias in aliases:
                if alias in data:
                    value = data[alias]
                    if value is None:
                        raise ValueError(f"Field '{field}' (alias '{alias}') cannot be None")
                    return value
            alias_list = ", ".join(aliases)
            raise ValueError(f"Missing required field '{field}' (aliases: {alias_list})")

        def optional(aliases: list[str], default: Any) -> Any:
            for alias in aliases:
                if alias in data:
                    return data[alias]
            return default

        ts_value = require("ts", ["ts", "timestamp"])
        open_value = require("open", ["open", "open_price", "o"])
        high_value = require("high", ["high", "high_price", "h"])
        low_value = require("low", ["low", "low_price", "l"])
        close_value = require("close", ["close", "close_price", "c"])
        volume_value = require("volume", ["volume", "volume_qty", "v"])
        is_closed_value = optional(["is_closed", "closed", "x"], True)

        if not isinstance(is_closed_value, bool):
            if isinstance(is_closed_value, str):
                normalized = is_closed_value.strip().lower()
                if normalized in {"true", "1", "yes", "closed"}:
                    is_closed_value = True
                elif normalized in {"false", "0", "no", "open"}:
                    is_closed_value = False
                else:
                    raise ValueError(f"Unrecognised boolean value for 'is_closed': {is_closed_value!r}")
            elif isinstance(is_closed_value, int | float):
                is_closed_value = bool(is_closed_value)
            else:
                raise ValueError(f"Unrecognised type for 'is_closed': {type(is_closed_value).__name__}")

        return cls(
            ts=coerce_timestamp(ts_value),
            open=coerce_price(open_value),
            high=coerce_price(high_value),
            low=coerce_price(low_value),
            close=coerce_price(close_value),
            volume=coerce_qty(volume_value),
            is_closed=is_closed_value,
        )
