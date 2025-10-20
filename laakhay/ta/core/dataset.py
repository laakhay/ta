"""Dataset - Multi-symbol/timeframe collection for technical analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator, Union, Optional, Set, TypeVar

from .ohlcv import OHLCV
from .series import Series
from .types import Symbol, Timestamp

T = TypeVar('T')


@dataclass(frozen=True)
class DatasetKey:
    """Immutable key for dataset series identification."""
    symbol: Symbol
    timeframe: str
    source: str = "default"

    def __str__(self) -> str:  # type: ignore[override]
        """String representation of the key."""
        return f"{self.symbol}_{self.timeframe}_{self.source}"


@dataclass(frozen=True)
class DatasetMetadata:
    """Metadata for the dataset."""
    created_at: Timestamp = field(default_factory=lambda: datetime.now(timezone.utc))
    description: str = ""
    tags: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary format."""
        return {
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "tags": list(self.tags)
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatasetMetadata:
        """Create metadata from dictionary format."""
        from .timestamps import coerce_timestamp
        
        return cls(
            created_at=coerce_timestamp(data.get("created_at", datetime.now(timezone.utc))),
            description=data.get("description", ""),
            tags=set(data.get("tags", []))
        )


class Dataset:
    """
    Multi-symbol/timeframe collection for technical analysis.
    
    Provides efficient storage and retrieval of OHLCV series data across
    multiple symbols, timeframes, and data sources.
    """
    
    def __init__(self, metadata: Optional[DatasetMetadata] = None):
        """Initialize dataset with optional metadata."""
        self._series: dict[DatasetKey, Union[OHLCV, Series[Any]]] = {}
        self.metadata = metadata or DatasetMetadata()
    
    def add_series(self, 
                  symbol: Symbol, 
                  timeframe: str, 
                  series: Union[OHLCV, Series[Any]], 
                  source: str = "default") -> None:
        """Add a series to the dataset."""
        key = DatasetKey(symbol=symbol, timeframe=timeframe, source=source)
        self._series[key] = series
    
    def series(self, 
               symbol: Symbol, 
               timeframe: str, 
               source: str = "default") -> Optional[Union[OHLCV, Series[Any]]]:
        """Retrieve a series from the dataset."""
        key = DatasetKey(symbol=symbol, timeframe=timeframe, source=source)
        return self._series.get(key)
    
    def select(self, 
               symbol: Optional[Symbol] = None,
               timeframe: Optional[str] = None,
               source: Optional[str] = None) -> DatasetView:
        """Create a filtered view of the dataset."""
        return DatasetView(self, symbol=symbol, timeframe=timeframe, source=source)
    
    @property
    def keys(self) -> Set[DatasetKey]:
        """Get all dataset keys."""
        return set(self._series.keys())
    
    @property
    def symbols(self) -> Set[Symbol]:
        """Get all symbols in the dataset."""
        return {key.symbol for key in self._series.keys()}
    
    @property
    def timeframes(self) -> Set[str]:
        """Get all timeframes in the dataset."""
        return {key.timeframe for key in self._series.keys()}
    
    @property
    def sources(self) -> Set[str]:
        """Get all sources in the dataset."""
        return {key.source for key in self._series.keys()}
    
    def __len__(self) -> int:
        """Number of series in the dataset."""
        return len(self._series)
    
    def __iter__(self) -> Iterator[tuple[DatasetKey, Union[OHLCV, Series[Any]]]]:
        """Iterate over key-series pairs."""
        return iter(self._series.items())
    
    def __contains__(self, key: DatasetKey) -> bool:
        """Check if a key exists in the dataset."""
        return key in self._series
    
    def __getitem__(self, key: DatasetKey) -> Union[OHLCV, Series[Any]]:
        """Get series by key."""
        if key not in self._series:
            raise KeyError(f"No series found for key: {key}")
        return self._series[key]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert dataset to dictionary format."""
        series_dict = {}
        for key, series in self._series.items():
            series_dict[str(key)] = series.to_dict()
        
        return {
            "metadata": self.metadata.to_dict(),
            "series": series_dict
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Dataset:
        """Create dataset from dictionary format."""
        metadata = DatasetMetadata.from_dict(data.get("metadata", {}))
        dataset = cls(metadata=metadata)
        
        # Import here to avoid circular imports
        from .ohlcv import OHLCV
        from .series import Series
        
        for key_str, series_data in data.get("series", {}).items():
            # Parse key from string representation
            parts = key_str.split("_")
            if len(parts) >= 2:
                symbol = parts[0]
                timeframe = parts[1]
                source = parts[2] if len(parts) > 2 else "default"
                
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
    
    def __init__(self, 
                 dataset: Dataset,
                 symbol: Optional[Symbol] = None,
                 timeframe: Optional[str] = None,
                 source: Optional[str] = None):
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
    
    def series(self, symbol: Symbol, timeframe: str, source: str = "default") -> Optional[Union[OHLCV, Series[Any]]]:
        """Retrieve a series from the view."""
        key = DatasetKey(symbol=symbol, timeframe=timeframe, source=source)
        if not self._matches_filter(key):
            return None
        return self._dataset.series(symbol, timeframe, source)
    
    @property
    def keys(self) -> Set[DatasetKey]:
        """Get all keys in the view."""
        return {key for key in self._dataset.keys if self._matches_filter(key)}
    
    @property
    def symbols(self) -> Set[Symbol]:
        """Get all symbols in the view."""
        return {key.symbol for key in self.keys}
    
    @property
    def timeframes(self) -> Set[str]:
        """Get all timeframes in the view."""
        return {key.timeframe for key in self.keys}
    
    @property
    def sources(self) -> Set[str]:
        """Get all sources in the view."""
        return {key.source for key in self.keys}
    
    def __len__(self) -> int:
        """Number of series in the view."""
        return len(self.keys)
    
    def __iter__(self) -> Iterator[tuple[DatasetKey, Union[OHLCV, Series[Any]]]]:
        """Iterate over filtered key-series pairs."""
        for key, series in self._dataset:
            if self._matches_filter(key):
                yield key, series
    
    def __contains__(self, key: DatasetKey) -> bool:
        """Check if a key exists in the view."""
        return key in self._dataset and self._matches_filter(key)
    
    def __getitem__(self, key: DatasetKey) -> Union[OHLCV, Series[Any]]:
        """Get series by key."""
        if key not in self:
            raise KeyError(f"No series found for key in view: {key}")
        return self._dataset[key]


def dataset(*series: Union[OHLCV, Series[Any]], 
           metadata: Optional[DatasetMetadata] = None,
           **kwargs: Union[OHLCV, Series[Any]]) -> Dataset:
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
        symbol = getattr(series_obj, 'symbol', f'SYMBOL_{i}')
        timeframe = getattr(series_obj, 'timeframe', '1h')
        source = getattr(series_obj, 'source', 'default')
        
        ds.add_series(symbol, timeframe, series_obj, source)
    
    # Add series passed as keyword arguments
    for key_str, series_obj in kwargs.items():
        # Parse key format: 'symbol_timeframe_source' or 'symbol_timeframe'
        parts = key_str.split('_')
        if len(parts) >= 2:
            symbol = parts[0]
            timeframe = parts[1]
            source = parts[2] if len(parts) > 2 else 'default'
            ds.add_series(symbol, timeframe, series_obj, source)
    
    return ds
