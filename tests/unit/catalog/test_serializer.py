"""Tests for output serialization functionality."""

from datetime import timezone, datetime, timedelta
UTC = timezone.utc
from decimal import Decimal

from laakhay.ta.catalog.serializer import OutputSerializer, serialize_series
from laakhay.ta.core import Series
from laakhay.ta.core.types import Price


def create_sample_series(count: int = 10) -> Series[Price]:
    """Create sample series for testing."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = tuple(base + timedelta(hours=i) for i in range(count))
    values = tuple(Price(Decimal(100 + i)) for i in range(count))
    return Series(timestamps=timestamps, values=values, symbol="BTCUSDT", timeframe="1h")


class TestOutputSerializer:
    """Test OutputSerializer class."""

    def test_serialize_series(self):
        """Test serializing a Series."""
        serializer = OutputSerializer()
        series = create_sample_series(5)
        result = serializer.serialize_series(series, "sma")

        assert isinstance(result, dict)
        assert "sma" in result
        assert len(result["sma"]) == 5
        for point in result["sma"]:
            assert "time" in point
            assert "value" in point
            assert isinstance(point["time"], int)
            assert isinstance(point["value"], float)

    def test_serialize_series_with_availability_mask(self):
        """Test serializing Series with availability mask."""
        serializer = OutputSerializer()
        base = datetime(2024, 1, 1, tzinfo=UTC)
        timestamps = tuple(base + timedelta(hours=i) for i in range(5))
        values = tuple(Price(Decimal(100 + i)) for i in range(5))
        # First 2 values are unavailable
        mask = (False, False, True, True, True)
        series = Series(timestamps=timestamps, values=values, symbol="BTCUSDT", timeframe="1h", availability_mask=mask)

        result = serializer.serialize_series(series, "sma")
        # Should only have 3 points (where mask is True)
        assert len(result["sma"]) == 3

    def test_serialize_result_series(self):
        """Test serializing a Series result."""
        serializer = OutputSerializer()
        series = create_sample_series(5)
        outputs, meta = serializer.serialize_result(series)

        assert isinstance(outputs, dict)
        assert isinstance(meta, dict)
        assert "result" in outputs
        assert len(outputs["result"]) == 5

    def test_serialize_result_dict(self):
        """Test serializing dict result."""
        serializer = OutputSerializer()
        result = {
            "macd": create_sample_series(5),
            "signal": create_sample_series(5),
        }
        outputs, meta = serializer.serialize_result(result)

        assert "macd" in outputs
        assert "signal" in outputs
        assert len(outputs["macd"]) == 5
        assert len(outputs["signal"]) == 5

    def test_serialize_result_tuple(self):
        """Test serializing tuple result with aliases."""
        serializer = OutputSerializer()
        series1 = create_sample_series(5)
        series2 = create_sample_series(5)
        result = (series1, series2)
        outputs, meta = serializer.serialize_result(result, output_names=("macd", "signal"))

        assert "macd" in outputs
        assert "signal" in outputs
        assert len(outputs["macd"]) == 5
        assert len(outputs["signal"]) == 5

    def test_serialize_result_scalar(self):
        """Test serializing scalar result."""
        serializer = OutputSerializer()
        outputs, meta = serializer.serialize_result(100.5)

        assert len(outputs) == 0
        assert "result" in meta
        assert meta["result"] == 100.5


class TestSerializeSeriesConvenience:
    """Test serialize_series convenience function."""

    def test_serialize_series_convenience(self):
        """Test convenience function."""
        series = create_sample_series(5)
        result = serialize_series(series, "sma")

        assert isinstance(result, dict)
        assert "sma" in result
        assert len(result["sma"]) == 5
