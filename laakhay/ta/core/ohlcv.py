"""OHLCV series container - manages a series of Bars with metadata."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from .bar import Bar
from .types import Price, Qty, Symbol, Timestamp


@dataclass(slots=True, frozen=True)
class OHLCV:
    """Immutable OHLCV container with columnar storage."""

    timestamps: tuple[Timestamp, ...]  # Shared timestamps
    opens: tuple[Price, ...]  # Open prices
    highs: tuple[Price, ...]  # High prices
    lows: tuple[Price, ...]  # Low prices
    closes: tuple[Price, ...]  # Close prices
    volumes: tuple[Qty, ...]  # Volumes
    is_closed: tuple[bool, ...]  # Closed flags
    symbol: Symbol
    timeframe: str

    def __post_init__(self) -> None:
        """Validate OHLCV data integrity after initialization."""
        lengths = {
            len(self.timestamps),
            len(self.opens),
            len(self.highs),
            len(self.lows),
            len(self.closes),
            len(self.volumes),
            len(self.is_closed),
        }
        if len(lengths) > 1:
            raise ValueError("All OHLCV data columns must have the same length")

        if len(self.timestamps) > 1:
            if any(later < earlier for earlier, later in zip(self.timestamps, self.timestamps[1:], strict=False)):
                raise ValueError("Timestamps must be sorted")

    @property
    def length(self) -> int:
        """Number of bars in the OHLCV series."""
        return len(self.timestamps)

    @property
    def is_empty(self) -> bool:
        """Whether the OHLCV series is empty."""
        return self.length == 0

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, index: int | slice) -> Bar | OHLCV:
        """Access single bar or slice the OHLCV series."""
        try:
            if isinstance(index, int):
                return Bar(
                    ts=self.timestamps[index],
                    open=self.opens[index],
                    high=self.highs[index],
                    low=self.lows[index],
                    close=self.closes[index],
                    volume=self.volumes[index],
                    is_closed=self.is_closed[index],
                )
            else:
                # Handle slice case
                return OHLCV(
                    timestamps=self.timestamps[index],
                    opens=self.opens[index],
                    highs=self.highs[index],
                    lows=self.lows[index],
                    closes=self.closes[index],
                    volumes=self.volumes[index],
                    is_closed=self.is_closed[index],
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                )
        except (TypeError, KeyError) as e:
            if "indices must be integers or slices" in str(e):
                raise TypeError("OHLCV indices must be integers or slices") from e
            raise

    def __iter__(self) -> Iterator[Bar]:
        """Iterate over Bar objects."""
        for i in range(len(self)):
            yield Bar(
                ts=self.timestamps[i],
                open=self.opens[i],
                high=self.highs[i],
                low=self.lows[i],
                close=self.closes[i],
                volume=self.volumes[i],
                is_closed=self.is_closed[i],
            )

    def slice_by_time(self, start: Timestamp, end: Timestamp) -> OHLCV:
        """Slice OHLCV by time range using binary search for efficiency."""
        if start > end:
            raise ValueError("Start time must be <= end time")

        # Binary search for start index
        left, right = 0, len(self.timestamps)
        while left < right:
            mid = (left + right) // 2
            if self.timestamps[mid] < start:
                left = mid + 1
            else:
                right = mid
        start_idx = left

        # Binary search for end index
        left, right = start_idx, len(self.timestamps)
        while left < right:
            mid = (left + right) // 2
            if self.timestamps[mid] <= end:
                left = mid + 1
            else:
                right = mid
        end_idx = left

        return OHLCV(
            timestamps=self.timestamps[start_idx:end_idx],
            opens=self.opens[start_idx:end_idx],
            highs=self.highs[start_idx:end_idx],
            lows=self.lows[start_idx:end_idx],
            closes=self.closes[start_idx:end_idx],
            volumes=self.volumes[start_idx:end_idx],
            is_closed=self.is_closed[start_idx:end_idx],
            symbol=self.symbol,
            timeframe=self.timeframe,
        )

    def to_series(self, field: str | None = None) -> Any:
        """Convert OHLCV to Series.

        - If field is None, return a dict of Series for all fields
        - If field is provided (one of: open, high, low, close, volume), return a single Series for that field
        """
        # Import here to avoid circular imports
        from .series import (  # type: ignore[import-untyped]
            PriceSeries,
            QtySeries,
            Series,
        )

        if field is None:
            return {
                "opens": PriceSeries(
                    timestamps=self.timestamps,
                    values=self.opens,
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                ),
                "highs": PriceSeries(
                    timestamps=self.timestamps,
                    values=self.highs,
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                ),
                "lows": PriceSeries(
                    timestamps=self.timestamps,
                    values=self.lows,
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                ),
                "closes": PriceSeries(
                    timestamps=self.timestamps,
                    values=self.closes,
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                ),
                "volumes": QtySeries(
                    timestamps=self.timestamps,
                    values=self.volumes,
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                ),
            }

        # Single-field mode
        if field == "open":
            values = self.opens
        elif field == "high":
            values = self.highs
        elif field == "low":
            values = self.lows
        elif field == "close":
            values = self.closes
        elif field == "volume":
            values = self.volumes
        else:
            raise ValueError(f"Unknown field: {field}. Must be one of: open, high, low, close, volume")

        return Series(
            timestamps=self.timestamps,
            values=values,
            symbol=self.symbol,
            timeframe=self.timeframe,
        )

    @classmethod
    def from_bars(cls, bars: list[Bar], symbol: str = "UNKNOWN", timeframe: str = "1h") -> OHLCV:
        """Create OHLCV from a list of Bar objects."""
        if not bars:
            raise ValueError("Cannot create OHLCV from empty bar list")

        timestamps = tuple(bar.ts for bar in bars)
        opens = tuple(bar.open for bar in bars)
        highs = tuple(bar.high for bar in bars)
        lows = tuple(bar.low for bar in bars)
        closes = tuple(bar.close for bar in bars)
        volumes = tuple(bar.volume for bar in bars)
        is_closed = tuple(bar.is_closed for bar in bars)

        return cls(
            timestamps=timestamps,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            is_closed=is_closed,
            symbol=symbol,
            timeframe=timeframe,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OHLCV:
        """Create OHLCV from dictionary format."""
        from .coercers import coerce_price, coerce_qty
        from .timestamps import coerce_timestamp

        timestamps = tuple(coerce_timestamp(ts) for ts in data["timestamps"])
        opens = tuple(coerce_price(price) for price in data["opens"])
        highs = tuple(coerce_price(price) for price in data["highs"])
        lows = tuple(coerce_price(price) for price in data["lows"])
        closes = tuple(coerce_price(price) for price in data["closes"])
        volumes = tuple(coerce_qty(vol) for vol in data["volumes"])
        is_closed = tuple(data.get("is_closed", [True] * len(timestamps)))

        return cls(
            timestamps=timestamps,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            is_closed=is_closed,
            symbol=data["symbol"],
            timeframe=data["timeframe"],
        )

    # Backwards-compatible alias for single-field access
    def to_series_field(self, field: str) -> Any:
        return self.to_series(field)

    def to_dict(self) -> dict[str, Any]:
        """Convert OHLCV to dictionary format."""
        return {
            "timestamps": [ts.isoformat() for ts in self.timestamps],
            "opens": [float(price) for price in self.opens],
            "highs": [float(price) for price in self.highs],
            "lows": [float(price) for price in self.lows],
            "closes": [float(price) for price in self.closes],
            "volumes": [float(vol) for vol in self.volumes],
            "is_closed": list(self.is_closed),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
        }
