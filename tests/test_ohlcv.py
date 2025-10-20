"""Tests for OHLCV data structure."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Any

from laakhay.ta.core import OHLCV
from laakhay.ta.core.bar import Bar
from laakhay.ta.core.types import Price, Timestamp


class TestOHLCVCreation:
    """Test OHLCV creation and validation."""

    def test_ohlcv_creation(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test basic OHLCV creation."""
        ohlcv = OHLCV(
            timestamps=sample_ohlcv_data["timestamps"],
            opens=sample_ohlcv_data["opens"],
            highs=sample_ohlcv_data["highs"],
            lows=sample_ohlcv_data["lows"],
            closes=sample_ohlcv_data["closes"],
            volumes=sample_ohlcv_data["volumes"],
            is_closed=sample_ohlcv_data["is_closed"],
            symbol=sample_ohlcv_data["symbol"],
            timeframe=sample_ohlcv_data["timeframe"],
            metadata=sample_ohlcv_data["metadata"]
        )
        
        assert len(ohlcv) == 4
        assert ohlcv.symbol == "BTCUSDT"
        assert ohlcv.timeframe == "1h"
        assert ohlcv.metadata == {"source": "test"}

    def test_ohlcv_creation_empty(self) -> None:
        """Test OHLCV creation with empty data."""
        ohlcv = OHLCV(
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
        
        assert len(ohlcv) == 0
        assert ohlcv.is_empty is True

    def test_ohlcv_validation_mismatched_lengths(self, sample_timestamps: tuple[Timestamp, ...], sample_price_values: tuple[Price, ...]) -> None:
        """Test OHLCV validation with mismatched lengths."""
        with pytest.raises(ValueError, match="All OHLCV data columns must have the same length"):
            OHLCV(
                timestamps=sample_timestamps,
                opens=sample_price_values[:2],  # Only 2 values, 4 timestamps
                highs=sample_price_values,
                lows=sample_price_values,
                closes=sample_price_values,
                volumes=(Decimal("1000"), Decimal("1500"), Decimal("800"), Decimal("1200")),
                is_closed=(True, True, True, True),
                symbol="BTCUSDT",
                timeframe="1h"
            )

    def test_ohlcv_validation_unsorted_timestamps(self, unsorted_timestamps: tuple[Timestamp, ...], sample_price_values: tuple[Price, ...]) -> None:
        """Test OHLCV validation with unsorted timestamps."""
        with pytest.raises(ValueError, match="Timestamps must be sorted"):
            OHLCV(
                timestamps=unsorted_timestamps,
                opens=sample_price_values[:3],
                highs=sample_price_values[:3],
                lows=sample_price_values[:3],
                closes=sample_price_values[:3],
                volumes=(Decimal("1000"), Decimal("1500"), Decimal("800")),
                is_closed=(True, True, True),
                symbol="BTCUSDT",
                timeframe="1h"
            )

    def test_ohlcv_validation_single_timestamp(self) -> None:
        """Test OHLCV validation with single timestamp (should pass)."""
        ts = datetime.now(timezone.utc)
        ohlcv = OHLCV(
            timestamps=(ts,),
            opens=(Decimal("100"),),
            highs=(Decimal("101"),),
            lows=(Decimal("99"),),
            closes=(Decimal("100.5"),),
            volumes=(Decimal("1000"),),
            is_closed=(True,),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        assert len(ohlcv) == 1


class TestOHLCVProperties:
    """Test OHLCV properties and methods."""

    def test_length_property(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test length property."""
        ohlcv = OHLCV(
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
        assert ohlcv.length == 4

    def test_is_empty_property(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test is_empty property."""
        ohlcv = OHLCV(
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
        assert ohlcv.is_empty is False

        empty_ohlcv = OHLCV(
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
        assert empty_ohlcv.is_empty is True

    def test_len_method(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test __len__ method."""
        ohlcv = OHLCV(
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
        assert len(ohlcv) == 4


class TestOHLCVIndexing:
    """Test OHLCV indexing and slicing."""

    def test_getitem_single_index(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test single index access returns Bar object."""
        ohlcv = OHLCV(
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
        
        bar = ohlcv[0]
        assert isinstance(bar, Bar)
        assert bar.ts == sample_ohlcv_data["timestamps"][0]
        assert bar.open == sample_ohlcv_data["opens"][0]
        assert bar.high == sample_ohlcv_data["highs"][0]
        assert bar.low == sample_ohlcv_data["lows"][0]
        assert bar.close == sample_ohlcv_data["closes"][0]
        assert bar.volume == sample_ohlcv_data["volumes"][0]
        assert bar.is_closed == sample_ohlcv_data["is_closed"][0]

    def test_getitem_slice(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test slice access returns OHLCV object."""
        ohlcv = OHLCV(
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
        
        sliced = ohlcv[1:3]
        assert isinstance(sliced, OHLCV)
        assert len(sliced) == 2
        assert sliced.timestamps == sample_ohlcv_data["timestamps"][1:3]
        assert sliced.opens == sample_ohlcv_data["opens"][1:3]
        assert sliced.symbol == ohlcv.symbol
        assert sliced.timeframe == ohlcv.timeframe

    def test_getitem_invalid_type(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test invalid index type."""
        ohlcv = OHLCV(
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
        
        with pytest.raises(TypeError, match="OHLCV indices must be integers or slices"):
            ohlcv["invalid"]  # type: ignore[arg-type]

    def test_getitem_out_of_bounds(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test out of bounds index access."""
        ohlcv = OHLCV(
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
        
        with pytest.raises(IndexError, match="tuple index out of range"):
            ohlcv[999]


class TestOHLCVIteration:
    """Test OHLCV iteration."""

    def test_iteration(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test OHLCV iteration yields Bar objects."""
        ohlcv = OHLCV(
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
        
        bars = list(ohlcv)
        assert len(bars) == 4
        for i, bar in enumerate(bars):
            assert isinstance(bar, Bar)
            assert bar.ts == sample_ohlcv_data["timestamps"][i]
            assert bar.open == sample_ohlcv_data["opens"][i]


class TestOHLCVTimeSlicing:
    """Test OHLCV time-based slicing."""

    def test_slice_by_time(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test time-based slicing."""
        ohlcv = OHLCV(
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
        
        start = sample_ohlcv_data["timestamps"][1]
        end = sample_ohlcv_data["timestamps"][2]
        
        sliced = ohlcv.slice_by_time(start, end)
        assert len(sliced) == 2
        assert sliced.timestamps[0] == start
        assert sliced.timestamps[-1] == end

    def test_slice_by_time_invalid_range(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test time-based slicing with invalid range."""
        ohlcv = OHLCV(
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
        
        start = sample_ohlcv_data["timestamps"][2]
        end = sample_ohlcv_data["timestamps"][1]  # End before start
        
        with pytest.raises(ValueError, match="Start time must be <= end time"):
            ohlcv.slice_by_time(start, end)

    def test_slice_by_time_no_matches(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test time-based slicing with no matches."""
        ohlcv = OHLCV(
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
        
        start = sample_ohlcv_data["timestamps"][-1] + timedelta(hours=1)
        end = start + timedelta(hours=1)
        
        sliced = ohlcv.slice_by_time(start, end)
        assert len(sliced) == 0


class TestOHLCVToSeries:
    """Test OHLCV to_series method."""

    def test_to_series(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test to_series method."""
        ohlcv = OHLCV(
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
        
        series_dict = ohlcv.to_series()
        assert len(series_dict) == 5
        assert "opens" in series_dict
        assert "highs" in series_dict
        assert "lows" in series_dict
        assert "closes" in series_dict
        assert "volumes" in series_dict
        
        # Check that all series have the same length and symbol
        for _, series in series_dict.items():
            assert len(series) == 4
            assert series.symbol == "BTCUSDT"
            assert series.timeframe == "1h"


class TestOHLCVFromBars:
    """Test OHLCV from_bars class method."""

    def test_from_bars(self, sample_bars: list[Bar]) -> None:
        """Test from_bars class method."""
        ohlcv = OHLCV.from_bars(sample_bars, symbol="BTCUSDT", timeframe="1h")
        
        assert len(ohlcv) == 4
        assert ohlcv.symbol == "BTCUSDT"
        assert ohlcv.timeframe == "1h"
        
        # Check that the first bar matches
        bar = ohlcv[0]
        assert isinstance(bar, Bar)
        assert bar.ts == sample_bars[0].ts
        assert bar.open == sample_bars[0].open

    def test_from_bars_empty_list(self) -> None:
        """Test from_bars with empty list."""
        with pytest.raises(ValueError, match="Cannot create OHLCV from empty bar list"):
            OHLCV.from_bars([])

    def test_from_bars_default_params(self, sample_bars: list[Bar]) -> None:
        """Test from_bars with default parameters."""
        ohlcv = OHLCV.from_bars(sample_bars)
        
        assert len(ohlcv) == 4
        assert ohlcv.symbol == "UNKNOWN"
        assert ohlcv.timeframe == "1h"


class TestOHLCVSerialization:
    """Test OHLCV serialization methods."""

    def test_to_dict(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test to_dict method."""
        ohlcv = OHLCV(
            timestamps=sample_ohlcv_data["timestamps"],
            opens=sample_ohlcv_data["opens"],
            highs=sample_ohlcv_data["highs"],
            lows=sample_ohlcv_data["lows"],
            closes=sample_ohlcv_data["closes"],
            volumes=sample_ohlcv_data["volumes"],
            is_closed=sample_ohlcv_data["is_closed"],
            symbol=sample_ohlcv_data["symbol"],
            timeframe=sample_ohlcv_data["timeframe"],
            metadata=sample_ohlcv_data["metadata"]
        )
        
        data = ohlcv.to_dict()
        assert data["symbol"] == "BTCUSDT"
        assert data["timeframe"] == "1h"
        assert data["metadata"] == {"source": "test"}
        assert len(data["timestamps"]) == 4
        assert len(data["opens"]) == 4
        assert len(data["volumes"]) == 4

    def test_from_dict(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test from_dict class method."""
        # Convert data to dict format
        data = {
            "timestamps": [ts.isoformat() for ts in sample_ohlcv_data["timestamps"]],
            "opens": [float(p) for p in sample_ohlcv_data["opens"]],
            "highs": [float(p) for p in sample_ohlcv_data["highs"]],
            "lows": [float(p) for p in sample_ohlcv_data["lows"]],
            "closes": [float(p) for p in sample_ohlcv_data["closes"]],
            "volumes": [float(v) for v in sample_ohlcv_data["volumes"]],
            "is_closed": list(sample_ohlcv_data["is_closed"]),
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "metadata": {"source": "test"}
        }
        
        ohlcv = OHLCV.from_dict(data)
        assert len(ohlcv) == 4
        assert ohlcv.symbol == "BTCUSDT"
        assert ohlcv.timeframe == "1h"
        assert ohlcv.metadata == {"source": "test"}

    def test_from_dict_default_is_closed(self, sample_ohlcv_data: dict[str, Any]) -> None:
        """Test from_dict with missing is_closed data."""
        data = {
            "timestamps": [ts.isoformat() for ts in sample_ohlcv_data["timestamps"]],
            "opens": [float(p) for p in sample_ohlcv_data["opens"]],
            "highs": [float(p) for p in sample_ohlcv_data["highs"]],
            "lows": [float(p) for p in sample_ohlcv_data["lows"]],
            "closes": [float(p) for p in sample_ohlcv_data["closes"]],
            "volumes": [float(v) for v in sample_ohlcv_data["volumes"]],
            "symbol": "BTCUSDT",
            "timeframe": "1h"
        }
        
        ohlcv = OHLCV.from_dict(data)
        assert len(ohlcv) == 4
        assert all(ohlcv.is_closed)  # Should default to True
