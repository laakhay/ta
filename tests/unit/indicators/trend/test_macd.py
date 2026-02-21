"""Tests for MACD indicator."""

from datetime import UTC, datetime

UTC = UTC
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.trend.macd import macd
from laakhay.ta.registry.models import SeriesContext


class TestMACDIndicator:
    """Test MACD (Moving Average Convergence Divergence) indicator."""

    def test_macd_basic_calculation(self):
        """Test basic MACD calculation with valid data."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 31)]  # 30 days
        values = [Decimal(str(100 + i)) for i in range(30)]  # 100, 101, ..., 129

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        macd_line, signal_line, histogram = macd(ctx, fast_period=12, slow_period=26, signal_period=9)

        # All should have same length as input
        assert macd_line.symbol == "BTCUSDT"
        assert signal_line.symbol == "BTCUSDT"
        assert histogram.symbol == "BTCUSDT"
        assert macd_line.timeframe == "1h"
        assert signal_line.timeframe == "1h"
        assert histogram.timeframe == "1h"

        assert len(macd_line.timestamps) == 30
        assert len(signal_line.timestamps) == 30
        assert len(histogram.timestamps) == 30

    def test_macd_empty_series(self):
        """Test MACD with empty input series."""
        close_series = Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h")

        ctx = SeriesContext(close=close_series)
        macd_line, signal_line, histogram = macd(ctx)

        assert macd_line.symbol == "BTCUSDT"
        assert signal_line.symbol == "BTCUSDT"
        assert histogram.symbol == "BTCUSDT"
        assert len(macd_line.timestamps) == 0
        assert len(signal_line.timestamps) == 0
        assert len(histogram.timestamps) == 0

    def test_macd_invalid_periods(self):
        """Test MACD with invalid period parameters."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal("100")]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)

        with pytest.raises(ValueError, match="MACD periods must be positive"):
            macd(ctx, fast_period=0, slow_period=26, signal_period=9)

        with pytest.raises(ValueError, match="MACD periods must be positive"):
            macd(ctx, fast_period=12, slow_period=0, signal_period=9)

        with pytest.raises(ValueError, match="MACD periods must be positive"):
            macd(ctx, fast_period=12, slow_period=26, signal_period=0)

        with pytest.raises(ValueError, match="Fast period must be less than slow period"):
            macd(ctx, fast_period=26, slow_period=12, signal_period=9)

    def test_macd_default_parameters(self):
        """Test MACD with default parameters."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 31)]  # 30 days
        values = [Decimal(str(100 + i)) for i in range(30)]  # 100, 101, ..., 129

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        macd_line, signal_line, histogram = macd(ctx)  # Use defaults: 12, 26, 9

        assert len(macd_line.timestamps) == 30
        assert len(signal_line.timestamps) == 30
        assert len(histogram.timestamps) == 30

    def test_macd_histogram_calculation(self):
        """Test that histogram = macd_line - signal_line."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 31)]  # 30 days
        values = [Decimal(str(100 + i)) for i in range(30)]  # 100, 101, ..., 129

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        macd_line, signal_line, histogram = macd(ctx, fast_period=12, slow_period=26, signal_period=9)

        # Verify histogram calculation
        for i in range(len(histogram.timestamps)):
            expected_hist = Decimal(str(macd_line.values[i])) - Decimal(str(signal_line.values[i]))
            assert abs(float(histogram.values[i]) - float(expected_hist)) < 0.01

    def test_macd_metadata_inheritance(self):
        """Test that MACD preserves input series metadata."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 31)]
        values = [Decimal(str(100 + i)) for i in range(30)]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h",
        )

        ctx = SeriesContext(close=close_series)
        macd_line, signal_line, histogram = macd(ctx)

        assert macd_line.symbol == "ETHUSDT"
        assert signal_line.symbol == "ETHUSDT"
        assert histogram.symbol == "ETHUSDT"
        assert macd_line.timeframe == "4h"
        assert signal_line.timeframe == "4h"
        assert histogram.timeframe == "4h"

    def test_macd_short_series(self):
        """Test MACD with series shorter than slow period."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 21)]  # 20 days
        values = [Decimal(str(100 + i)) for i in range(20)]  # 100, 101, ..., 119

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        macd_line, signal_line, histogram = macd(ctx, fast_period=12, slow_period=26, signal_period=9)

        # Should still return series of same length
        assert len(macd_line.timestamps) == 20
        assert len(signal_line.timestamps) == 20
        assert len(histogram.timestamps) == 20
