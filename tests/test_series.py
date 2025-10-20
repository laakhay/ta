"""Tests for Series data structure."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Any

from laakhay.ta.core import Series, PriceSeries, QtySeries
from laakhay.ta.core.types import Price, Qty, Timestamp


class TestSeriesCreation:
    """Test Series creation and validation."""

    def test_series_creation(self, sample_series_data: dict[str, Any]) -> None:
        """Test basic Series creation."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"],
            metadata=sample_series_data["metadata"]
        )
        
        assert len(series) == 4
        assert series.symbol == "BTCUSDT"
        assert series.timeframe == "1h"
        assert series.metadata == {"source": "test"}

    def test_series_creation_empty(self, empty_series_data: dict[str, Any]) -> None:
        """Test Series creation with empty data."""
        series = Series[Price](
            timestamps=empty_series_data["timestamps"],
            values=empty_series_data["values"],
            symbol=empty_series_data["symbol"],
            timeframe=empty_series_data["timeframe"],
            metadata=empty_series_data["metadata"]
        )
        
        assert len(series) == 0
        assert series.is_empty is True

    def test_series_validation_mismatched_lengths(self, sample_timestamps: tuple[Timestamp, ...]) -> None:
        """Test Series validation with mismatched lengths."""
        with pytest.raises(ValueError, match="Timestamps and values must have the same length"):
            Series[Price](
                timestamps=sample_timestamps,
                values=(Decimal("100"), Decimal("101")),  # Only 2 values, 4 timestamps
                symbol="BTCUSDT",
                timeframe="1h"
            )

    def test_series_validation_unsorted_timestamps(self, unsorted_timestamps: tuple[Timestamp, ...]) -> None:
        """Test Series validation with unsorted timestamps."""
        with pytest.raises(ValueError, match="Timestamps must be sorted"):
            Series[Price](
                timestamps=unsorted_timestamps,
                values=(Decimal("100"), Decimal("101"), Decimal("102")),
                symbol="BTCUSDT",
                timeframe="1h"
            )

    def test_series_validation_single_timestamp(self) -> None:
        """Test Series validation with single timestamp (should pass)."""
        ts = datetime.now(timezone.utc)
        series = Series[Price](
            timestamps=(ts,),
            values=(Decimal("100"),),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        assert len(series) == 1


class TestSeriesProperties:
    """Test Series properties and methods."""

    def test_length_property(self, sample_series_data: dict[str, Any]) -> None:
        """Test length property."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"]
        )
        assert series.length == 4

    def test_is_empty_property(self, sample_series_data: dict[str, Any], empty_series_data: dict[str, Any]) -> None:
        """Test is_empty property."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"]
        )
        assert series.is_empty is False

        empty_series = Series[Price](
            timestamps=empty_series_data["timestamps"],
            values=empty_series_data["values"],
            symbol=empty_series_data["symbol"],
            timeframe=empty_series_data["timeframe"]
        )
        assert empty_series.is_empty is True

    def test_len_method(self, sample_series_data: dict[str, Any]) -> None:
        """Test __len__ method."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"]
        )
        assert len(series) == 4


class TestSeriesIndexing:
    """Test Series indexing and slicing."""

    def test_getitem_single_index(self, sample_series_data: dict[str, Any]) -> None:
        """Test single index access."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"]
        )
        
        timestamp, value = series[0]
        assert timestamp == sample_series_data["timestamps"][0]
        assert value == sample_series_data["values"][0]

    def test_getitem_slice(self, sample_series_data: dict[str, Any]) -> None:
        """Test slice access."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"]
        )
        
        sliced = series[1:3]
        assert isinstance(sliced, Series)
        assert len(sliced) == 2
        assert sliced.timestamps == sample_series_data["timestamps"][1:3]
        assert sliced.values == sample_series_data["values"][1:3]
        assert sliced.symbol == series.symbol
        assert sliced.timeframe == series.timeframe

    def test_getitem_invalid_type(self, sample_series_data: dict[str, Any]) -> None:
        """Test invalid index type."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"]
        )
        
        with pytest.raises(TypeError, match="Series indices must be integers or slices"):
            series["invalid"]  # type: ignore[arg-type]

    def test_getitem_out_of_bounds(self, sample_series_data: dict[str, Any]) -> None:
        """Test out of bounds index access."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"]
        )
        
        with pytest.raises(IndexError, match="tuple index out of range"):
            series[999]


class TestSeriesIteration:
    """Test Series iteration."""

    def test_iteration(self, sample_series_data: dict[str, Any]) -> None:
        """Test Series iteration."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"]
        )
        
        items = list(series)
        assert len(items) == 4
        for i, (timestamp, value) in enumerate(items):
            assert timestamp == sample_series_data["timestamps"][i]
            assert value == sample_series_data["values"][i]


class TestSeriesOperations:
    """Test Series operations."""

    def test_add_series(self, sample_series_data: dict[str, Any]) -> None:
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

    def test_add_series_different_symbol(self, sample_series_data: dict[str, Any]) -> None:
        """Test adding Series with different symbols."""
        series1 = Series[Price](
            timestamps=sample_series_data["timestamps"][:2],
            values=sample_series_data["values"][:2],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        series2 = Series[Price](
            timestamps=sample_series_data["timestamps"][2:],
            values=sample_series_data["values"][2:],
            symbol="ETHUSDT",  # Different symbol
            timeframe="1h"
        )
        
        with pytest.raises(ValueError, match="Cannot add series with different symbols or timeframes"):
            series1 + series2  # type: ignore[reportUnusedExpression]

    def test_add_series_different_timeframe(self, sample_series_data: dict[str, Any]) -> None:
        """Test adding Series with different timeframes."""
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
            timeframe="4h"  # Different timeframe
        )
        
        with pytest.raises(ValueError, match="Cannot add series with different symbols or timeframes"):
            series1 + series2  # type: ignore[reportUnusedExpression]

    def test_add_scalar(self, sample_series_data: dict[str, Any]) -> None:
        """Test adding scalar to Series."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        result = series + Decimal("10")
        assert len(result) == 4
        assert result[0][1] == sample_series_data["values"][0] + Decimal("10")

    def test_add_scalar_invalid_type(self, sample_series_data: dict[str, Any]) -> None:
        """Test adding invalid scalar type."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        with pytest.raises(TypeError, match="Cannot add"):
            series + "invalid"  # type: ignore[arg-type]


class TestSeriesTimeSlicing:
    """Test Series time-based slicing."""

    def test_slice_by_time(self, sample_series_data: dict[str, Any]) -> None:
        """Test time-based slicing."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        start = sample_series_data["timestamps"][1]
        end = sample_series_data["timestamps"][2]
        
        sliced = series.slice_by_time(start, end)
        assert len(sliced) == 2
        assert sliced.timestamps[0] == start
        assert sliced.timestamps[-1] == end

    def test_slice_by_time_invalid_range(self, sample_series_data: dict[str, Any]) -> None:
        """Test time-based slicing with invalid range."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        start = sample_series_data["timestamps"][2]
        end = sample_series_data["timestamps"][1]  # End before start
        
        with pytest.raises(ValueError, match="Start time must be <= end time"):
            series.slice_by_time(start, end)

    def test_slice_by_time_no_matches(self, sample_series_data: dict[str, Any]) -> None:
        """Test time-based slicing with no matches."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        start = sample_series_data["timestamps"][-1] + timedelta(hours=1)
        end = start + timedelta(hours=1)
        
        sliced = series.slice_by_time(start, end)
        assert len(sliced) == 0


class TestSeriesSerialization:
    """Test Series serialization methods."""

    def test_to_dict(self, sample_series_data: dict[str, Any]) -> None:
        """Test to_dict method."""
        series = Series[Price](
            timestamps=sample_series_data["timestamps"],
            values=sample_series_data["values"],
            symbol=sample_series_data["symbol"],
            timeframe=sample_series_data["timeframe"],
            metadata=sample_series_data["metadata"]
        )
        
        data = series.to_dict()
        assert data["symbol"] == "BTCUSDT"
        assert data["timeframe"] == "1h"
        assert data["metadata"] == {"source": "test"}
        assert len(data["timestamps"]) == 4
        assert len(data["values"]) == 4

    def test_from_dict(self, sample_series_data: dict[str, Any]) -> None:
        """Test from_dict class method."""
        # Convert timestamps to ISO format for from_dict
        data = {
            "timestamps": [ts.isoformat() for ts in sample_series_data["timestamps"]],
            "values": [float(v) for v in sample_series_data["values"]],
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "metadata": {"source": "test"}
        }
        
        series = Series[Price].from_dict(data)
        assert len(series) == 4
        assert series.symbol == "BTCUSDT"
        assert series.timeframe == "1h"
        assert series.metadata == {"source": "test"}


class TestSeriesTypeAliases:
    """Test Series type aliases."""

    def test_price_series(self, sample_timestamps: tuple[Timestamp, ...], sample_price_values: tuple[Price, ...]) -> None:
        """Test PriceSeries type alias."""
        series = PriceSeries(
            timestamps=sample_timestamps,
            values=sample_price_values,
            symbol="BTCUSDT",
            timeframe="1h"
        )
        assert isinstance(series, Series)
        assert len(series) == 4

    def test_qty_series(self, sample_timestamps: tuple[Timestamp, ...], sample_volumes: tuple[Qty, ...]) -> None:
        """Test QtySeries type alias."""
        series = QtySeries(
            timestamps=sample_timestamps,
            values=sample_volumes,
            symbol="BTCUSDT",
            timeframe="1h"
        )
        assert isinstance(series, Series)
        assert len(series) == 4
