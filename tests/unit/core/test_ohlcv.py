"""Tests for OHLCV data structure."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Any

from laakhay.ta.core import OHLCV
from laakhay.ta.core.bar import Bar
from laakhay.ta.core.types import Timestamp


class TestOHLCVCore:
    """Core OHLCV functionality tests."""

    @pytest.fixture
    def ohlcv(self, sample_ohlcv_data: dict[str, Any]) -> OHLCV:
        """Create a standard OHLCV for testing."""
        return OHLCV(
            timestamps=sample_ohlcv_data["timestamps"],
            opens=sample_ohlcv_data["opens"],
            highs=sample_ohlcv_data["highs"],
            lows=sample_ohlcv_data["lows"],
            closes=sample_ohlcv_data["closes"],
            volumes=sample_ohlcv_data["volumes"],
            is_closed=sample_ohlcv_data["is_closed"],
            symbol=sample_ohlcv_data["symbol"],
            timeframe=sample_ohlcv_data["timeframe"]
        )

    @pytest.fixture
    def empty_ohlcv(self) -> OHLCV:
        """Create an empty OHLCV for testing."""
        return OHLCV(
            timestamps=(),
            opens=(),
            highs=(),
            lows=(),
            closes=(),
            volumes=(),
            is_closed=(),
            symbol="BTCUSDT",
            timeframe="1h"
        )

    def test_creation(self, ohlcv: OHLCV) -> None:
        """Test basic OHLCV creation and properties."""
        assert len(ohlcv) == 4
        assert ohlcv.length == 4
        assert ohlcv.symbol == "BTCUSDT"
        assert ohlcv.timeframe == "1h"
        assert not ohlcv.is_empty

    def test_empty_creation(self, empty_ohlcv: OHLCV) -> None:
        """Test empty OHLCV creation."""
        assert len(empty_ohlcv) == 0
        assert empty_ohlcv.length == 0
        assert empty_ohlcv.is_empty

    def test_validation_errors(self, sample_timestamps: tuple[Timestamp, ...]) -> None:
        """Test validation error scenarios."""
        # Mismatched lengths
        with pytest.raises(ValueError, match="All OHLCV data columns must have the same length"):
            OHLCV(
                timestamps=sample_timestamps,
                opens=(Decimal("100"),),  # Only 1 value, 4 timestamps
                highs=(Decimal("101"),),  # Wrong type - should be Price
                lows=(Decimal("99"),),
                closes=(Decimal("101"),),
                volumes=(Decimal("1000"),),
                is_closed=(True,),
                symbol="BTCUSDT",
                timeframe="1h"
            )

        # Unsorted timestamps
        unsorted_ts = (datetime.now(timezone.utc), datetime.now(timezone.utc) - timedelta(hours=1))
        with pytest.raises(ValueError, match="Timestamps must be sorted"):
            OHLCV(
                timestamps=unsorted_ts,
                opens=(Decimal("100"), Decimal("101")),
                highs=(Decimal("102"), Decimal("103")),
                lows=(Decimal("99"), Decimal("100")),
                closes=(Decimal("101"), Decimal("102")),
                volumes=(Decimal("1000"), Decimal("1100")),
                is_closed=(True, True),
                symbol="BTCUSDT",
                timeframe="1h"
            )

    def test_indexing(self, ohlcv: OHLCV) -> None:
        """Test indexing and slicing."""
        # Single index - returns Bar
        bar = ohlcv[0]
        assert isinstance(bar, Bar)
        assert bar.ts == ohlcv.timestamps[0]
        assert bar.open == ohlcv.opens[0]
        assert bar.high == ohlcv.highs[0]
        assert bar.low == ohlcv.lows[0]
        assert bar.close == ohlcv.closes[0]
        assert bar.volume == ohlcv.volumes[0]
        assert bar.is_closed == ohlcv.is_closed[0]

        # Slice - returns OHLCV
        sliced = ohlcv[1:3]
        assert isinstance(sliced, OHLCV)
        assert len(sliced) == 2
        assert sliced.timestamps == ohlcv.timestamps[1:3]
        assert sliced.opens == ohlcv.opens[1:3]

        # Out of bounds
        with pytest.raises(IndexError):
            ohlcv[999]

        # Invalid index type
        with pytest.raises(TypeError, match="OHLCV indices must be integers or slices"):
            ohlcv["invalid"]  # type: ignore

    def test_iteration(self, ohlcv: OHLCV) -> None:
        """Test iteration over OHLCV."""
        bars = list(ohlcv)
        assert len(bars) == 4
        for i, bar in enumerate(bars):
            assert isinstance(bar, Bar)
            assert bar.ts == ohlcv.timestamps[i]
            assert bar.open == ohlcv.opens[i]

    def test_time_slicing(self, ohlcv: OHLCV) -> None:
        """Test time-based slicing."""
        start = ohlcv.timestamps[1]
        end = ohlcv.timestamps[2]
        
        sliced = ohlcv.slice_by_time(start, end)
        assert len(sliced) == 2
        assert sliced.timestamps[0] >= start
        assert sliced.timestamps[-1] <= end

        # Invalid range
        with pytest.raises(ValueError, match="Start time must be <= end time"):
            ohlcv.slice_by_time(end, start)

        # No matches
        future_start = ohlcv.timestamps[-1] + timedelta(hours=1)
        future_end = future_start + timedelta(hours=1)
        empty_slice = ohlcv.slice_by_time(future_start, future_end)
        assert len(empty_slice) == 0


class TestOHLCVConversion:
    """Test OHLCV conversion methods."""

    @pytest.fixture
    def ohlcv(self, sample_ohlcv_data: dict[str, Any]) -> OHLCV:
        """Create a standard OHLCV for testing."""
        return OHLCV(
            timestamps=sample_ohlcv_data["timestamps"],
            opens=sample_ohlcv_data["opens"],
            highs=sample_ohlcv_data["highs"],
            lows=sample_ohlcv_data["lows"],
            closes=sample_ohlcv_data["closes"],
            volumes=sample_ohlcv_data["volumes"],
            is_closed=sample_ohlcv_data["is_closed"],
            symbol=sample_ohlcv_data["symbol"],
            timeframe=sample_ohlcv_data["timeframe"]
        )

    def test_to_series(self, ohlcv: OHLCV) -> None:
        """Test converting OHLCV to Series objects."""
        series_dict = ohlcv.to_series()
        
        assert "opens" in series_dict
        assert "highs" in series_dict
        assert "lows" in series_dict
        assert "closes" in series_dict
        assert "volumes" in series_dict
        
        # Check that all series have the same length and metadata
        for _name, series in series_dict.items():
            assert len(series) == len(ohlcv)
            assert series.symbol == ohlcv.symbol
            assert series.timeframe == ohlcv.timeframe

    def test_from_bars(self, sample_bars: list[Bar]) -> None:
        """Test creating OHLCV from Bar objects."""
        ohlcv = OHLCV.from_bars(sample_bars, symbol="BTCUSDT", timeframe="1h")
        
        assert len(ohlcv) == 4
        assert ohlcv.symbol == "BTCUSDT"
        assert ohlcv.timeframe == "1h"
        
        # Check first bar matches
        first_bar = ohlcv[0]
        assert isinstance(first_bar, Bar)
        assert first_bar.ts == sample_bars[0].ts
        assert first_bar.open == sample_bars[0].open

        # Test empty list raises error
        with pytest.raises(ValueError, match="Cannot create OHLCV from empty bar list"):
            OHLCV.from_bars([])

        # Test with default parameters
        ohlcv_default = OHLCV.from_bars(sample_bars)
        assert ohlcv_default.symbol == "UNKNOWN"
        assert ohlcv_default.timeframe == "1h"


class TestOHLCVSerialization:
    """Test OHLCV serialization methods."""

    @pytest.fixture
    def ohlcv(self, sample_ohlcv_data: dict[str, Any]) -> OHLCV:
        """Create a standard OHLCV for testing."""
        return OHLCV(
            timestamps=sample_ohlcv_data["timestamps"],
            opens=sample_ohlcv_data["opens"],
            highs=sample_ohlcv_data["highs"],
            lows=sample_ohlcv_data["lows"],
            closes=sample_ohlcv_data["closes"],
            volumes=sample_ohlcv_data["volumes"],
            is_closed=sample_ohlcv_data["is_closed"],
            symbol=sample_ohlcv_data["symbol"],
            timeframe=sample_ohlcv_data["timeframe"]
        )

    def test_serialization(self, ohlcv: OHLCV) -> None:
        """Test to_dict and from_dict methods."""
        # Test to_dict
        data = ohlcv.to_dict()
        assert data["symbol"] == "BTCUSDT"
        assert data["timeframe"] == "1h"
        assert len(data["timestamps"]) == 4
        assert len(data["opens"]) == 4
        assert len(data["highs"]) == 4
        assert len(data["lows"]) == 4
        assert len(data["closes"]) == 4
        assert len(data["volumes"]) == 4
        assert len(data["is_closed"]) == 4

        # Test from_dict
        restored = OHLCV.from_dict(data)
        assert len(restored) == 4
        assert restored.symbol == "BTCUSDT"
        assert restored.timeframe == "1h"
        assert restored.timestamps == ohlcv.timestamps
        assert restored.opens == ohlcv.opens

    def test_from_dict_defaults(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test from_dict with missing is_closed field."""
        data = {
            "timestamps": [ts.isoformat() for ts in sample_ohlcv_data["timestamps"]],
            "opens": [float(price) for price in sample_ohlcv_data["opens"]],
            "highs": [float(price) for price in sample_ohlcv_data["highs"]],
            "lows": [float(price) for price in sample_ohlcv_data["lows"]],
            "closes": [float(price) for price in sample_ohlcv_data["closes"]],
            "volumes": [float(vol) for vol in sample_ohlcv_data["volumes"]],
            "symbol": "BTCUSDT",
            "timeframe": "1h"
            # Missing is_closed field
        }
        
        ohlcv = OHLCV.from_dict(data)
        assert len(ohlcv) == 4
        assert all(ohlcv.is_closed)  # Should default to all True