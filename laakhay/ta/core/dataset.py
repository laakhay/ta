"""Dataset - Multi-symbol/timeframe collection for technical analysis."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, TypeVar

from .ohlcv import OHLCV
from .series import Series
from .types import Symbol, Timestamp

if TYPE_CHECKING:
    from ..registry.models import SeriesContext

T = TypeVar("T")


@dataclass(frozen=True)
class DatasetKey:
    """Immutable key for dataset series identification."""

    symbol: Symbol
    timeframe: str
    source: str = "default"

    def __str__(self) -> str:  # type: ignore[override]
        """String representation of the key using structured format."""
        # Use a structured format that can handle underscores in symbols
        # Format: "symbol|timeframe|source" to avoid conflicts with underscores
        return f"{self.symbol}|{self.timeframe}|{self.source}"

    def to_dict(self) -> dict[str, str]:
        """Convert key to dictionary format for safe serialization."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> DatasetKey:
        """Create key from dictionary format."""
        return cls(
            symbol=data["symbol"],
            timeframe=data["timeframe"],
            source=data.get("source", "default"),
        )


@dataclass(frozen=True)
class DatasetMetadata:
    """Metadata for the dataset."""

    created_at: Timestamp = field(default_factory=lambda: datetime.now(UTC))
    description: str = ""
    tags: set[str] = field(default_factory=lambda: set())

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary format."""
        return {
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatasetMetadata:
        """Create metadata from dictionary format."""
        from .timestamps import coerce_timestamp

        return cls(
            created_at=coerce_timestamp(data.get("created_at", datetime.now(UTC))),
            description=data.get("description", ""),
            tags=set(data.get("tags", [])),
        )


class Dataset:
    """
    Multi-symbol/timeframe collection for technical analysis.

    Provides efficient storage and retrieval of OHLCV series data across
    multiple symbols, timeframes, and data sources.
    """

    def __init__(self, metadata: DatasetMetadata | None = None):
        """Initialize dataset with optional metadata."""
        self._series: dict[DatasetKey, OHLCV | Series[Any]] = {}
        self.metadata = metadata or DatasetMetadata()

    def add_series(
        self,
        symbol: Symbol,
        timeframe: str,
        series: OHLCV | Series[Any],
        source: str = "default",
    ) -> None:
        """Add a series to the dataset."""
        key = DatasetKey(symbol=symbol, timeframe=timeframe, source=source)
        self._series[key] = series

    def add(self, symbol: Symbol, timeframe: str, source: str, series: OHLCV | Series[Any]) -> None:
        """Add a series to the dataset (alias for add_series with different parameter order)."""
        self.add_series(symbol, timeframe, series, source)

    def to_context(self) -> SeriesContext:
        """Convert dataset to SeriesContext for indicator evaluation.

        This method extracts series from the dataset and creates a SeriesContext
        that can be used with indicator functions.

        Returns:
            SeriesContext with available series

        Raises:
            ValueError: If no suitable series are found in the dataset
        """
        from ..registry.models import SeriesContext

        # Build context dictionary from available series
        context_dict = {}

        for key, series in self._series.items():
            # Handle OHLCV data
            if hasattr(series, "to_series"):  # It's an OHLCV
                context_dict["close"] = series.to_series("close")
                context_dict["open"] = series.to_series("open")
                context_dict["high"] = series.to_series("high")
                context_dict["low"] = series.to_series("low")
                context_dict["volume"] = series.to_series("volume")
                context_dict["price"] = series.to_series("close")  # Use close as default price
            else:
                # Handle regular Series
                if key.source == "close":
                    context_dict["close"] = series
                elif key.source == "high":
                    context_dict["high"] = series
                elif key.source == "low":
                    context_dict["low"] = series
                elif key.source == "open":
                    context_dict["open"] = series
                elif key.source == "volume":
                    context_dict["volume"] = series
                elif key.source == "price":
                    context_dict["price"] = series
                else:
                    # Use the source name as the attribute name
                    context_dict[key.source] = series

        # If no close series found but we have series with values, use the first one as close
        if "close" not in context_dict and self._series:
            first_series = next(iter(self._series.values()))
            if hasattr(first_series, "values") and len(first_series.values) > 0:
                context_dict["close"] = first_series

        if not context_dict:
            # Return empty context for empty dataset
            return SeriesContext()

        return SeriesContext(**context_dict)

    def series(self, symbol: Symbol, timeframe: str, source: str = "default") -> OHLCV | Series[Any] | None:
        """Retrieve a series from the dataset."""
        key = DatasetKey(symbol=symbol, timeframe=timeframe, source=source)
        return self._series.get(key)

    def select(
        self,
        symbol: Symbol | None = None,
        timeframe: str | None = None,
        source: str | None = None,
    ) -> DatasetView:
        """Create a filtered view of the dataset."""
        return DatasetView(self, symbol=symbol, timeframe=timeframe, source=source)

    @property
    def keys(self) -> set[DatasetKey]:
        """Get all dataset keys."""
        return set(self._series.keys())

    @property
    def symbols(self) -> set[Symbol]:
        """Get all symbols in the dataset."""
        return {key.symbol for key in self._series.keys()}

    @property
    def timeframes(self) -> set[str]:
        """Get all timeframes in the dataset."""
        return {key.timeframe for key in self._series.keys()}

    @property
    def sources(self) -> set[str]:
        """Get all sources in the dataset."""
        return {key.source for key in self._series.keys()}

    def __len__(self) -> int:
        """Number of series in the dataset."""
        return len(self._series)

    @property
    def is_empty(self) -> bool:
        """Whether the dataset is empty."""
        return len(self._series) == 0

    def __iter__(self) -> Iterator[tuple[DatasetKey, OHLCV | Series[Any]]]:
        """Iterate over key-series pairs."""
        return iter(self._series.items())

    def __contains__(self, key: DatasetKey) -> bool:
        """Check if a key exists in the dataset."""
        return key in self._series

    def __getitem__(self, key: DatasetKey | str) -> OHLCV | Series[Any]:
        """Get series by key or field name."""
        # Handle string field access (e.g., "close", "open", "high", "low", "volume")
        if isinstance(key, str):
            if key in ["open", "high", "low", "close", "volume"]:
                # Get the first OHLCV series and extract the field
                if not self._series:
                    raise KeyError("No series found in dataset")

                # Find the first OHLCV series
                ohlcv_series = None
                for series in self._series.values():
                    if hasattr(series, "to_series"):  # It's an OHLCV
                        ohlcv_series = series
                        break

                if ohlcv_series is None:
                    raise KeyError(f"No OHLCV series found for field access: {key}")

                return ohlcv_series.to_series(key)
            else:
                # Try to find a series with this symbol
                for series_key, series in self._series.items():
                    if series_key.symbol == key:
                        return series
                raise KeyError(f"No series found with symbol: {key}")

        # Handle DatasetKey access
        if key not in self._series:
            raise KeyError(f"No series found for key: {key}")
        return self._series[key]

    def build_context(self, symbol: Symbol, timeframe: str, required_fields: list[str]) -> SeriesContext:
        """Build a SeriesContext for a specific symbol/timeframe using only required fields.

        Prefers OHLCV series when present; falls back to individual source series.
        """
        from ..registry.models import SeriesContext

        # Try to find an OHLCV for this symbol/timeframe
        ohlcv: OHLCV | None = None
        for key, series in self._series.items():
            if key.symbol == symbol and key.timeframe == timeframe and hasattr(series, "to_series"):
                ohlcv = series  # type: ignore[assignment]
                break

        ctx: dict[str, Series[Any]] = {}
        if ohlcv is not None:
            ctx.setdefault("open", ohlcv.to_series("open"))  # type: ignore[arg-type]
            ctx.setdefault("high", ohlcv.to_series("high"))  # type: ignore[arg-type]
            ctx.setdefault("low", ohlcv.to_series("low"))  # type: ignore[arg-type]
            ctx.setdefault("close", ohlcv.to_series("close"))  # type: ignore[arg-type]
            ctx.setdefault("price", ohlcv.to_series("close"))  # type: ignore[arg-type]
            try:
                ctx.setdefault("volume", ohlcv.to_series("volume"))  # type: ignore[arg-type]
            except (KeyError, AttributeError, ValueError):
                pass
        for required_field in required_fields:
            if ohlcv is not None and required_field in {
                "open",
                "high",
                "low",
                "close",
                "volume",
                "price",
            }:
                src_name = "close" if required_field == "price" else required_field
                key_name = "price" if required_field == "price" else required_field
                ctx[key_name] = ohlcv.to_series(src_name)  # type: ignore[arg-type]
                continue
            # Fallback to individual series by source
            found = False
            for key, series in self._series.items():
                if key.symbol == symbol and key.timeframe == timeframe:
                    wanted = required_field if required_field != "price" else "close"
                    if key.source == wanted:
                        ctx[required_field] = series  # type: ignore[assignment]
                        found = True
                        break
            if not found and required_field == "price":
                # try close as default
                for key, series in self._series.items():
                    if key.symbol == symbol and key.timeframe == timeframe and key.source == "close":
                        ctx["price"] = series  # type: ignore[assignment]
                        found = True
                        break
        return SeriesContext(**ctx)

    def to_dict(self) -> dict[str, Any]:
        """Convert dataset to dictionary format."""
        series_dict = {}
        for key, series in self._series.items():
            series_dict[str(key)] = series.to_dict()

        return {"metadata": self.metadata.to_dict(), "series": series_dict}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Dataset:
        """Create dataset from dictionary format."""
        metadata = DatasetMetadata.from_dict(data.get("metadata", {}))
        dataset = cls(metadata=metadata)

        # Import here to avoid circular imports
        from .ohlcv import OHLCV
        from .series import Series

        for key_str, series_data in data.get("series", {}).items():
            # Parse key from new structured format: symbol|timeframe|source
            parts = key_str.split("|")
            if len(parts) >= 2:
                symbol = parts[0]
                timeframe = parts[1]
                source = parts[2] if len(parts) > 2 else "default"
            else:
                continue

            # Determine series type and create appropriate object
            if "opens" in series_data and "highs" in series_data:
                # OHLCV data
                series = OHLCV.from_dict(series_data)
            else:
                # Series data
                series = Series[Any].from_dict(series_data)

            dataset.add_series(symbol, timeframe, series, source)

        return dataset


class DatasetView:
    """
    Filtered view of a dataset.

    Provides a read-only view of a dataset with optional filtering
    by symbol, timeframe, and source.
    """

    def __init__(
        self,
        dataset: Dataset,
        symbol: Symbol | None = None,
        timeframe: str | None = None,
        source: str | None = None,
    ):
        """Initialize dataset view with filters."""
        self._dataset = dataset
        self._symbol_filter = symbol
        self._timeframe_filter = timeframe
        self._source_filter = source

    def _matches_filter(self, key: DatasetKey) -> bool:
        """Check if key matches the view filters."""
        if self._symbol_filter and key.symbol != self._symbol_filter:
            return False
        if self._timeframe_filter and key.timeframe != self._timeframe_filter:
            return False
        if self._source_filter and key.source != self._source_filter:
            return False
        return True

    def series(self, symbol: Symbol, timeframe: str, source: str = "default") -> OHLCV | Series[Any] | None:
        """Retrieve a series from the view."""
        key = DatasetKey(symbol=symbol, timeframe=timeframe, source=source)
        if not self._matches_filter(key):
            return None
        return self._dataset.series(symbol, timeframe, source)

    @property
    def keys(self) -> set[DatasetKey]:
        """Get all keys in the view."""
        return {key for key in self._dataset.keys if self._matches_filter(key)}

    @property
    def symbols(self) -> set[Symbol]:
        """Get all symbols in the view."""
        return {key.symbol for key in self.keys}

    @property
    def timeframes(self) -> set[str]:
        """Get all timeframes in the view."""
        return {key.timeframe for key in self.keys}

    @property
    def sources(self) -> set[str]:
        """Get all sources in the view."""
        return {key.source for key in self.keys}

    def __len__(self) -> int:
        """Number of series in the view."""
        return len(self.keys)

    def __iter__(self) -> Iterator[tuple[DatasetKey, OHLCV | Series[Any]]]:
        """Iterate over filtered key-series pairs."""
        for key, series in self._dataset:
            if self._matches_filter(key):
                yield key, series

    def __contains__(self, key: DatasetKey) -> bool:
        """Check if a key exists in the view."""
        return key in self._dataset and self._matches_filter(key)

    def __getitem__(self, key: DatasetKey) -> OHLCV | Series[Any]:
        """Get series by key."""
        if key not in self:
            raise KeyError(f"No series found for key in view: {key}")
        return self._dataset[key]

    def to_context(self) -> SeriesContext:
        """Convert dataset to SeriesContext for indicator evaluation.

        This method extracts series from the dataset and creates a SeriesContext
        that can be used with indicator functions.

        Returns:
            SeriesContext with available series

        Raises:
            ValueError: If no suitable series are found in the dataset
        """
        from ..registry.models import SeriesContext

        # Build context dictionary from available series
        context_dict = {}

        for key, series in self:
            if hasattr(series, "to_series"):
                context_dict["close"] = series.to_series("close")
                context_dict["open"] = series.to_series("open")
                context_dict["high"] = series.to_series("high")
                context_dict["low"] = series.to_series("low")
                context_dict["volume"] = series.to_series("volume")
                context_dict["price"] = series.to_series("close")
            else:
                if key.source == "close":
                    context_dict["close"] = series
                elif key.source == "high":
                    context_dict["high"] = series
                elif key.source == "low":
                    context_dict["low"] = series
                elif key.source == "open":
                    context_dict["open"] = series
                elif key.source == "volume":
                    context_dict["volume"] = series
                elif key.source == "price":
                    context_dict["price"] = series
                else:
                    context_dict[key.source] = series

        if "close" not in context_dict and context_dict:
            # Fallback: use the first available series as close
            name, first_series = next(iter(context_dict.items()))
            context_dict.setdefault("close", first_series)

        return SeriesContext(**context_dict)


def dataset(
    *series: OHLCV | Series[Any],
    metadata: DatasetMetadata | None = None,
    **kwargs: OHLCV | Series[Any],
) -> Dataset:
    """
    Convenience function to create a dataset from multiple series.

    Args:
        *series: Variable number of series to add to dataset
        metadata: Optional dataset metadata
        **kwargs: Additional series with keys as 'symbol_timeframe_source'

    Returns:
        Dataset containing the provided series
    """
    ds = Dataset(metadata=metadata)

    # Add series passed as positional arguments
    for i, series_obj in enumerate(series):
        # Extract symbol and timeframe from series metadata or use defaults
        symbol = getattr(series_obj, "symbol", f"SYMBOL_{i}")
        timeframe = getattr(series_obj, "timeframe", "1h")
        source = getattr(series_obj, "source", "default")

        ds.add_series(symbol, timeframe, series_obj, source)

    # Add series passed as keyword arguments
    for key_str, series_obj in kwargs.items():
        # Parse key format: 'symbol|timeframe|source'
        parts = key_str.split("|")
        if len(parts) >= 2:
            symbol = parts[0]
            timeframe = parts[1]
            source = parts[2] if len(parts) > 2 else "default"
            ds.add_series(symbol, timeframe, series_obj, source)

    return ds
