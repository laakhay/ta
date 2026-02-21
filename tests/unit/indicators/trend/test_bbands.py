"""Tests for Bollinger Bands indicator."""

from datetime import UTC, datetime

UTC = UTC
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.trend.bbands import bb_lower, bb_upper, bbands
from laakhay.ta.registry.models import SeriesContext


class TestBollingerBandsIndicator:
    """Test Bollinger Bands indicator."""

    def test_bbands_basic_calculation(self):
        """Test basic Bollinger Bands calculation with valid data."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 26)]  # 25 days
        values = [Decimal(str(100 + i)) for i in range(25)]  # 100, 101, ..., 124

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        upper_band, middle_band, lower_band = bbands(ctx, period=20, std_dev=2.0)

        # All should have same length (period-1 shorter than input)
        assert upper_band.symbol == "BTCUSDT"
        assert middle_band.symbol == "BTCUSDT"
        assert lower_band.symbol == "BTCUSDT"
        assert upper_band.timeframe == "1h"
        assert middle_band.timeframe == "1h"
        assert lower_band.timeframe == "1h"

        assert len(upper_band.timestamps) == 6  # 25 - 20 + 1
        assert len(middle_band.timestamps) == 6
        assert len(lower_band.timestamps) == 6

    def test_bbands_empty_series(self):
        """Test Bollinger Bands with empty input series."""
        close_series = Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h")

        ctx = SeriesContext(close=close_series)
        upper_band, middle_band, lower_band = bbands(ctx)

        assert upper_band.symbol == "BTCUSDT"
        assert middle_band.symbol == "BTCUSDT"
        assert lower_band.symbol == "BTCUSDT"
        assert len(upper_band.timestamps) == 0
        assert len(middle_band.timestamps) == 0
        assert len(lower_band.timestamps) == 0

    def test_bbands_insufficient_data(self):
        """Test Bollinger Bands with insufficient data for period."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 11)]  # 10 days
        values = [Decimal(str(100 + i)) for i in range(10)]  # 100, 101, ..., 109

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        upper_band, middle_band, lower_band = bbands(ctx, period=20)

        # Should return empty series when period > data length
        assert len(upper_band.timestamps) == 0
        assert len(middle_band.timestamps) == 0
        assert len(lower_band.timestamps) == 0

    def test_bbands_invalid_parameters(self):
        """Test Bollinger Bands with invalid parameters."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal("100")]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)

        with pytest.raises(ValueError, match="Bollinger Bands period and std_dev must be positive"):
            bbands(ctx, period=0)

        with pytest.raises(ValueError, match="Bollinger Bands period and std_dev must be positive"):
            bbands(ctx, period=-1)

        with pytest.raises(ValueError, match="Bollinger Bands period and std_dev must be positive"):
            bbands(ctx, period=20, std_dev=0)

        with pytest.raises(ValueError, match="Bollinger Bands period and std_dev must be positive"):
            bbands(ctx, period=20, std_dev=-1)

    def test_bbands_default_parameters(self):
        """Test Bollinger Bands with default parameters."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 26)]  # 25 days
        values = [Decimal(str(100 + i)) for i in range(25)]  # 100, 101, ..., 124

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        upper_band, middle_band, lower_band = bbands(ctx)  # Use defaults: period=20, std_dev=2.0

        assert len(upper_band.timestamps) == 6  # 25 - 20 + 1
        assert len(middle_band.timestamps) == 6
        assert len(lower_band.timestamps) == 6

    def test_bbands_band_relationships(self):
        """Test that upper_band > middle_band > lower_band."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 26)]  # 25 days
        values = [Decimal(str(100 + i)) for i in range(25)]  # 100, 101, ..., 124

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        upper_band, middle_band, lower_band = bbands(ctx, period=20, std_dev=2.0)

        # Verify band relationships
        for i in range(len(upper_band.timestamps)):
            assert upper_band.values[i] > middle_band.values[i]
            assert middle_band.values[i] > lower_band.values[i]

    def test_bbands_metadata_inheritance(self):
        """Test that Bollinger Bands preserves input series metadata."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 26)]
        values = [Decimal(str(100 + i)) for i in range(25)]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h",
        )

        ctx = SeriesContext(close=close_series)
        upper_band, middle_band, lower_band = bbands(ctx)

        assert upper_band.symbol == "ETHUSDT"
        assert middle_band.symbol == "ETHUSDT"
        assert lower_band.symbol == "ETHUSDT"
        assert upper_band.timeframe == "4h"
        assert middle_band.timeframe == "4h"
        assert lower_band.timeframe == "4h"

    def test_bbands_different_std_dev(self):
        """Test Bollinger Bands with different standard deviation multipliers."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 26)]  # 25 days
        values = [Decimal(str(100 + i)) for i in range(25)]  # 100, 101, ..., 124

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)

        # Test with std_dev=1.0
        upper1, middle1, lower1 = bbands(ctx, period=20, std_dev=1.0)

        # Test with std_dev=3.0
        upper3, middle3, lower3 = bbands(ctx, period=20, std_dev=3.0)

        # Higher std_dev should result in wider bands
        for i in range(len(upper1.timestamps)):
            assert upper3.values[i] > upper1.values[i]
            assert lower1.values[i] > lower3.values[i]

    def test_bb_upper_wrapper_matches_bbands(self):
        """bb_upper should return the same upper band as bbands."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 26)]
        values = [Decimal(str(100 + i)) for i in range(25)]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        upper_band, middle_band, lower_band = bbands(ctx, period=20, std_dev=2.0)
        upper_wrapper = bb_upper(ctx, period=20, std_dev=2.0)

        assert upper_wrapper.symbol == upper_band.symbol
        assert upper_wrapper.timeframe == upper_band.timeframe
        assert upper_wrapper.timestamps == upper_band.timestamps
        assert upper_wrapper.values == upper_band.values

    def test_bb_lower_wrapper_matches_bbands(self):
        """bb_lower should return the same lower band as bbands."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 26)]
        values = [Decimal(str(100 + i)) for i in range(25)]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        upper_band, middle_band, lower_band = bbands(ctx, period=20, std_dev=2.0)
        lower_wrapper = bb_lower(ctx, period=20, std_dev=2.0)

        assert lower_wrapper.symbol == lower_band.symbol
        assert lower_wrapper.timeframe == lower_band.timeframe
        assert lower_wrapper.timestamps == lower_band.timestamps
        assert lower_wrapper.values == lower_band.values
