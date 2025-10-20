"""Tests for Series data structure."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Any

from laakhay.ta.core import Series, PriceSeries, QtySeries
from laakhay.ta.core.types import Price, Qty, Timestamp


class TestSeriesCore:
    """Core Series functionality tests."""

    @pytest.fixture
    def series(self, sample_series_data: dict[str, Any]) -> Series[Price]:
        """Create a standard Series for testing."""
        return Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"]
        )

    @pytest.fixture
    def empty_series(self) -> Series[Price]:
        """Create an empty Series for testing."""
        return Series[Price](
            timestamps=(),
            values=(),
            symbol="BTCUSDT",
            timeframe="1h"
        )

    def test_creation(self, series: Series[Price]) -> None:
        """Test basic Series creation and properties."""
        assert len(series) == 4
        assert series.length == 4
        assert series.symbol == "BTCUSDT"
        assert series.timeframe == "1h"
        assert not series.is_empty

    def test_empty_creation(self, empty_series: Series[Price]) -> None:
        """Test empty Series creation."""
        assert len(empty_series) == 0
        assert empty_series.length == 0
        assert empty_series.is_empty

    def test_validation_errors(self, sample_timestamps: tuple[Timestamp, ...]) -> None:
        """Test validation error scenarios."""
        # Mismatched lengths
        with pytest.raises(ValueError, match="Timestamps and values must have the same length"):
            Series[Price](
                timestamps=sample_timestamps,
                values=(Decimal("100"), Decimal("101")),  # Only 2 values, 4 timestamps
                symbol="BTCUSDT",
                timeframe="1h"
            )

        # Unsorted timestamps
        unsorted_ts = (datetime.now(timezone.utc), datetime.now(timezone.utc) - timedelta(hours=1))
        with pytest.raises(ValueError, match="Timestamps must be sorted"):
            Series[Price](
                timestamps=unsorted_ts,
                values=(Decimal("100"), Decimal("101")),
                symbol="BTCUSDT",
                timeframe="1h"
            )

    def test_indexing(self, series: Series[Price]) -> None:
        """Test indexing and slicing."""
        # Single index
        timestamp, value = series[0]
        assert timestamp == series.timestamps[0]
        assert value == series.values[0]

        # Slice
        sliced = series[1:3]
        assert isinstance(sliced, Series)
        assert len(sliced) == 2
        assert sliced.timestamps == series.timestamps[1:3]
        assert sliced.values == series.values[1:3]

        # Out of bounds
        with pytest.raises(IndexError):
            series[999]

        # Invalid index type
        with pytest.raises(TypeError, match="Series indices must be integers or slices"):
            series["invalid"]  # type: ignore

    def test_iteration(self, series: Series[Price]) -> None:
        """Test iteration over Series."""
        items = list(series)
        assert len(items) == 4
        for i, (timestamp, value) in enumerate(items):
            assert timestamp == series.timestamps[i]
            assert value == series.values[i]

    def test_time_slicing(self, series: Series[Price]) -> None:
        """Test time-based slicing."""
        start = series.timestamps[1]
        end = series.timestamps[2]
        
        sliced = series.slice_by_time(start, end)
        assert len(sliced) == 2
        assert sliced.timestamps[0] >= start
        assert sliced.timestamps[-1] <= end

        # Invalid range
        with pytest.raises(ValueError, match="Start time must be <= end time"):
            series.slice_by_time(end, start)

        # No matches
        future_start = series.timestamps[-1] + timedelta(hours=1)
        future_end = future_start + timedelta(hours=1)
        empty_slice = series.slice_by_time(future_start, future_end)
        assert len(empty_slice) == 0


class TestSeriesOperations:
    """Test Series arithmetic operations."""

    def test_series_addition(self, sample_series_data: dict[str, Any]) -> None:
        """Test adding two Series."""
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"][:2],
            values=sample_series_data["values"][:2],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"][2:],
            values=sample_series_data["values"][2:],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        combined = series1 + series2
        assert len(combined) == 4
        assert combined.symbol == "BTCUSDT"
        assert combined.timeframe == "1h"

    def test_addition_validation(self, sample_series_data: dict[str, Any]) -> None:
        """Test addition validation errors."""
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"][:2],
            values=sample_series_data["values"][:2],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        # Different symbol
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"][2:],
            values=sample_series_data["values"][2:],
            symbol="ETHUSDT",
            timeframe="1h"
        )
        
        with pytest.raises(ValueError, match="Cannot add series with different symbols or timeframes"):
            series1 + series2  # type: ignore[reportUnusedExpression]

        # Different timeframe
        series3 = Series[Price](
            timestamps=sample_series_data["timestamps"][2:],
            values=sample_series_data["values"][2:],
            symbol="BTCUSDT",
            timeframe="5m"
        )
        
        with pytest.raises(ValueError, match="Cannot add series with different symbols or timeframes"):
            series1 + series3  # type: ignore[reportUnusedExpression]

    def test_scalar_addition(self, sample_series_data: dict[str, Any]) -> None:
        """Test adding scalar to Series."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        result = series + Decimal("10")
        assert len(result) == len(series)
        assert result[0][1] == series[0][1] + Decimal("10")
        assert result.symbol == series.symbol
        assert result.timeframe == series.timeframe

        # Invalid scalar type
        with pytest.raises(TypeError):
            series + "invalid"  # type: ignore


class TestSeriesSerialization:
    """Test Series serialization methods."""

    @pytest.fixture
    def series(self, sample_series_data: dict[str, Any]) -> Series[Price]:
        """Create a standard Series for testing."""
        return Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"]
        )

    def test_serialization(self, series: Series[Price]) -> None:
        """Test to_dict and from_dict methods."""
        # Test to_dict
        data = series.to_dict()
        assert data["symbol"] == "BTCUSDT"
        assert data["timeframe"] == "1h"
        assert len(data["timestamps"]) == 4
        assert len(data["values"]) == 4

        # Test from_dict
        restored = Series[Price].from_dict(data)
        assert len(restored) == 4
        assert restored.symbol == "BTCUSDT"
        assert restored.timeframe == "1h"
        assert restored.timestamps == series.timestamps
        assert restored.values == series.values


class TestSeriesTypes:
    """Test Series type aliases."""

    def test_type_aliases(self, sample_timestamps: tuple[Timestamp, ...], sample_price_values: tuple[Price, ...]) -> None:
        """Test Series type aliases work correctly."""
        # Test PriceSeries
        price_series = PriceSeries(
            timestamps=sample_timestamps,
            values=sample_price_values,
            symbol="BTCUSDT",
            timeframe="1h"
        )
        assert isinstance(price_series, Series)
        assert len(price_series) == 4

        # Test QtySeries
        qty_series = QtySeries(
            timestamps=sample_timestamps,
            values=sample_price_values,  # Using price values for simplicity
            symbol="BTCUSDT",
            timeframe="1h"
        )
        assert isinstance(qty_series, Series)
        assert len(qty_series) == 4