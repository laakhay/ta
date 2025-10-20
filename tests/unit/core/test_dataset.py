"""Tests for Dataset functionality."""

import pytest
from datetime import datetime
from typing import Any

from laakhay.ta.core import (
    Dataset, DatasetKey, DatasetMetadata,
    OHLCV, Series
)
from laakhay.ta.core.dataset import dataset
from laakhay.ta.core.types import Price


class TestDatasetKey:
    """Test DatasetKey functionality."""

    def test_dataset_key_creation(self) -> None:
        """Test DatasetKey creation."""
        key = DatasetKey(symbol="BTCUSDT", timeframe="1h", source="binance")
        assert key.symbol == "BTCUSDT"
        assert key.timeframe == "1h"
        assert key.source == "binance"

    def test_dataset_key_default_source(self) -> None:
        """Test DatasetKey with default source."""
        key = DatasetKey(symbol="BTCUSDT", timeframe="1h")
        assert key.symbol == "BTCUSDT"
        assert key.timeframe == "1h"
        assert key.source == "default"

    def test_dataset_key_string_representation(self) -> None:
        """Test DatasetKey string representation."""
        key = DatasetKey(symbol="BTCUSDT", timeframe="1h", source="binance")
        assert str(key) == "BTCUSDT_1h_binance"

    def test_dataset_key_immutable(self) -> None:
        """Test that DatasetKey is immutable."""
        key = DatasetKey(symbol="BTCUSDT", timeframe="1h")
        with pytest.raises(AttributeError):
            key.symbol = "ETHUSDT"  # type: ignore[misc]


class TestDatasetMetadata:
    """Test DatasetMetadata functionality."""

    def test_dataset_metadata_creation(self) -> None:
        """Test DatasetMetadata creation."""
        metadata = DatasetMetadata(
            description="Test dataset",
            tags={"crypto", "test"}
        )
        assert metadata.description == "Test dataset"
        assert metadata.tags == {"crypto", "test"}
        assert isinstance(metadata.created_at, datetime)

    def test_dataset_metadata_defaults(self) -> None:
        """Test DatasetMetadata with defaults."""
        metadata = DatasetMetadata()
        assert metadata.description == ""
        assert metadata.tags == set()
        assert isinstance(metadata.created_at, datetime)

    def test_dataset_metadata_to_dict(self) -> None:
        """Test DatasetMetadata to_dict method."""
        metadata = DatasetMetadata(
            description="Test dataset",
            tags={"crypto", "test"}
        )
        data = metadata.to_dict()
        assert data["description"] == "Test dataset"
        assert set(data["tags"]) == {"crypto", "test"}
        assert "created_at" in data

    def test_dataset_metadata_from_dict(self) -> None:
        """Test DatasetMetadata from_dict method."""
        data = {
            "description": "Test dataset",
            "tags": ["crypto", "test"],
            "created_at": "2024-01-01T00:00:00Z"
        }
        metadata = DatasetMetadata.from_dict(data)
        assert metadata.description == "Test dataset"
        assert metadata.tags == {"crypto", "test"}
        assert isinstance(metadata.created_at, datetime)


class TestDatasetCreation:
    """Test Dataset creation and basic functionality."""

    def test_dataset_creation_empty(self) -> None:
        """Test empty dataset creation."""
        ds = Dataset()
        assert len(ds) == 0
        assert len(ds.symbols) == 0
        assert len(ds.timeframes) == 0
        assert len(ds.sources) == 0

    def test_dataset_creation_with_metadata(self) -> None:
        """Test dataset creation with metadata."""
        metadata = DatasetMetadata(description="Test dataset")
        ds = Dataset(metadata=metadata)
        assert ds.metadata.description == "Test dataset"

    def test_dataset_add_series(self, sample_series_data: dict[str, Any]) -> None:
        """Test adding series to dataset."""
        ds = Dataset()
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series)
        assert len(ds) == 1
        assert "BTCUSDT" in ds.symbols
        assert "1h" in ds.timeframes

    def test_dataset_add_series_with_source(self, sample_series_data: dict[str, Any]) -> None:
        """Test adding series with custom source."""
        ds = Dataset()
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series, source="binance")
        assert len(ds) == 1
        assert "binance" in ds.sources

    def test_dataset_series_retrieval(self, sample_series_data: dict[str, Any]) -> None:
        """Test series retrieval from dataset."""
        ds = Dataset()
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series)
        
        retrieved = ds.series("BTCUSDT", "1h")
        assert retrieved is not None
        assert len(retrieved) == len(series)

    def test_dataset_series_retrieval_not_found(self) -> None:
        """Test series retrieval when not found."""
        ds = Dataset()
        retrieved = ds.series("NONEXISTENT", "1h")
        assert retrieved is None

    def test_dataset_properties(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset properties."""
        ds = Dataset()
        
        # Add multiple series
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="ETHUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series1)
        ds.add_series("ETHUSDT", "1h", series2)
        
        assert len(ds) == 2
        assert ds.symbols == {"BTCUSDT", "ETHUSDT"}
        assert ds.timeframes == {"1h"}
        assert ds.sources == {"default"}

    def test_dataset_iteration(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset iteration."""
        ds = Dataset()
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series)
        
        items = list(ds)
        assert len(items) == 1
        key, retrieved_series = items[0]
        assert key.symbol == "BTCUSDT"
        assert key.timeframe == "1h"
        assert len(retrieved_series) == len(series)

    def test_dataset_contains(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset contains functionality."""
        ds = Dataset()
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series)
        
        key = DatasetKey("BTCUSDT", "1h")
        assert key in ds
        
        non_existent_key = DatasetKey("ETHUSDT", "1h")
        assert non_existent_key not in ds

    def test_dataset_getitem(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset getitem functionality."""
        ds = Dataset()
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series)
        
        key = DatasetKey("BTCUSDT", "1h")
        retrieved = ds[key]
        assert len(retrieved) == len(series)

    def test_dataset_getitem_not_found(self) -> None:
        """Test dataset getitem when key not found."""
        ds = Dataset()
        key = DatasetKey("NONEXISTENT", "1h")
        
        with pytest.raises(KeyError):
            ds[key]


class TestDatasetView:
    """Test DatasetView functionality."""

    def test_dataset_view_creation(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset view creation."""
        ds = Dataset()
        
        # Add multiple series
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="ETHUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series1)
        ds.add_series("ETHUSDT", "1h", series2)
        
        # Create view filtered by symbol
        btc_view = ds.select(symbol="BTCUSDT")
        assert len(btc_view) == 1
        assert btc_view.symbols == {"BTCUSDT"}

    def test_dataset_view_symbol_filter(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset view with symbol filter."""
        ds = Dataset()
        
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="ETHUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series1)
        ds.add_series("ETHUSDT", "1h", series2)
        
        btc_view = ds.select(symbol="BTCUSDT")
        assert len(btc_view) == 1
        assert "BTCUSDT" in btc_view.symbols
        assert "ETHUSDT" not in btc_view.symbols

    def test_dataset_view_timeframe_filter(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset view with timeframe filter."""
        ds = Dataset()
        
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="5m"
        )
        
        ds.add_series("BTCUSDT", "1h", series1)
        ds.add_series("BTCUSDT", "5m", series2)
        
        hourly_view = ds.select(timeframe="1h")
        assert len(hourly_view) == 1
        assert hourly_view.timeframes == {"1h"}

    def test_dataset_view_source_filter(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset view with source filter."""
        ds = Dataset()
        
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series1, source="binance")
        ds.add_series("BTCUSDT", "1h", series2, source="coinbase")
        
        binance_view = ds.select(source="binance")
        assert len(binance_view) == 1
        assert binance_view.sources == {"binance"}

    def test_dataset_view_multiple_filters(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset view with multiple filters."""
        ds = Dataset()
        
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="ETHUSDT",
            timeframe="1h"
        )
        series3 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="5m"
        )
        
        ds.add_series("BTCUSDT", "1h", series1)
        ds.add_series("ETHUSDT", "1h", series2)
        ds.add_series("BTCUSDT", "5m", series3)
        
        # Filter by symbol and timeframe
        filtered_view = ds.select(symbol="BTCUSDT", timeframe="1h")
        assert len(filtered_view) == 1
        assert filtered_view.symbols == {"BTCUSDT"}
        assert filtered_view.timeframes == {"1h"}

    def test_dataset_view_iteration(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset view iteration."""
        ds = Dataset()
        
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="ETHUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series1)
        ds.add_series("ETHUSDT", "1h", series2)
        
        btc_view = ds.select(symbol="BTCUSDT")
        items = list(btc_view)
        assert len(items) == 1
        key, _series = items[0]
        assert key.symbol == "BTCUSDT"


class TestDatasetConvenienceFunction:
    """Test dataset convenience function."""

    def test_dataset_function_positional_args(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset function with positional arguments."""
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="ETHUSDT",
            timeframe="1h"
        )
        
        ds = dataset(series1, series2)
        assert len(ds) == 2
        assert "BTCUSDT" in ds.symbols
        assert "ETHUSDT" in ds.symbols

    def test_dataset_function_with_metadata(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset function with metadata."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        metadata = DatasetMetadata(description="Test dataset")
        ds = dataset(series, metadata=metadata)
        assert ds.metadata.description == "Test dataset"

    def test_dataset_function_keyword_args(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset function with keyword arguments."""
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="ETHUSDT",
            timeframe="1h"
        )
        
        ds = dataset(
            BTCUSDT_1h=series1,
            ETHUSDT_1h=series2
        )
        assert len(ds) == 2
        assert "BTCUSDT" in ds.symbols
        assert "ETHUSDT" in ds.symbols

    def test_dataset_function_with_source(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset function with source specification."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ds = dataset(
            BTCUSDT_1h_binance=series
        )
        assert len(ds) == 1
        assert "binance" in ds.sources


class TestDatasetSerialization:
    """Test Dataset serialization functionality."""

    def test_dataset_to_dict(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset to_dict method."""
        ds = Dataset()
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series)
        
        data = ds.to_dict()
        assert "metadata" in data
        assert "series" in data
        assert len(data["series"]) == 1

    def test_dataset_from_dict(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset from_dict method."""
        # Create original dataset
        ds = Dataset()
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        ds.add_series("BTCUSDT", "1h", series)
        
        # Convert to dict and back
        data = ds.to_dict()
        restored_ds = Dataset.from_dict(data)
        
        assert len(restored_ds) == 1
        assert "BTCUSDT" in restored_ds.symbols

    def test_dataset_ohlcv_serialization(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test dataset serialization with OHLCV data."""
        ds = Dataset()
        ohlcv = OHLCV(
            timestamps=sample_ohlcv_data["timestamps"],
            opens=sample_ohlcv_data["opens"],
            highs=sample_ohlcv_data["highs"],
            lows=sample_ohlcv_data["lows"],
            closes=sample_ohlcv_data["closes"],
            volumes=sample_ohlcv_data["volumes"],
            is_closed=sample_ohlcv_data["is_closed"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", ohlcv)
        
        # Convert to dict and back
        data = ds.to_dict()
        restored_ds = Dataset.from_dict(data)
        
        assert len(restored_ds) == 1
        retrieved = restored_ds.series("BTCUSDT", "1h")
        assert retrieved is not None
        assert isinstance(retrieved, OHLCV)


class TestDatasetIntegration:
    """Test Dataset integration with real-world scenarios."""

    def test_multi_symbol_timeframe_dataset(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset with multiple symbols and timeframes."""
        ds = Dataset()
        
        # Add multiple series with different symbols and timeframes
        btc_1h = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        btc_5m = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="5m"
        )
        eth_1h = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="ETHUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", btc_1h)
        ds.add_series("BTCUSDT", "5m", btc_5m)
        ds.add_series("ETHUSDT", "1h", eth_1h)
        
        assert len(ds) == 3
        assert ds.symbols == {"BTCUSDT", "ETHUSDT"}
        assert ds.timeframes == {"1h", "5m"}
        
        # Test views
        btc_view = ds.select(symbol="BTCUSDT")
        assert len(btc_view) == 2
        
        hourly_view = ds.select(timeframe="1h")
        assert len(hourly_view) == 2

    def test_dataset_with_different_sources(self, sample_series_data: dict[str, Any]) -> None:
        """Test dataset with different data sources."""
        ds = Dataset()
        
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ds.add_series("BTCUSDT", "1h", series1, source="binance")
        ds.add_series("BTCUSDT", "1h", series2, source="coinbase")
        
        assert len(ds) == 2
        assert ds.sources == {"binance", "coinbase"}
        
        # Test source-specific retrieval
        binance_data = ds.series("BTCUSDT", "1h", source="binance")
        coinbase_data = ds.series("BTCUSDT", "1h", source="coinbase")
        
        assert binance_data is not None
        assert coinbase_data is not None
        assert binance_data is not coinbase_data
