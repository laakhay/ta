"""Tests for Bollinger Bands indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.trend.bbands import bbands
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
        # Calculate with period=20, std_dev=2.0
        upper_band, middle_band, lower_band = bbands(ctx, period=20, std_dev=2.0)

        assert upper_band.symbol == "BTCUSDT"
        assert middle_band.symbol == "BTCUSDT"
        assert lower_band.symbol == "BTCUSDT"
        assert upper_band.timeframe == "1h"

        assert len(upper_band.timestamps) == 25
        assert len(middle_band.timestamps) == 25
        assert len(lower_band.timestamps) == 25

        # available from index 19 (period 20)
        assert upper_band.availability_mask[18] is False
        assert upper_band.availability_mask[19] is True

    def test_bbands_empty_series(self):
        """Test BBands with empty input series."""
        close_series = Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h")
        ctx = SeriesContext(close=close_series)
        upper, middle, lower = bbands(ctx)
        assert len(upper.timestamps) == 0

    def test_bbands_insufficient_data(self):
        """Test BBands with insufficient data for period."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 11)]  # 10 days
        values = [Decimal(str(100 + i)) for i in range(10)]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        upper, middle, lower = bbands(ctx, period=20)

        assert len(upper.timestamps) == 10
        assert not any(upper.availability_mask)

    def test_bbands_invalid_parameters(self):
        """Test BBands with invalid parameters."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 3)]
        values = [Decimal("100"), Decimal("101")]
        close_series = Series[Price](
            timestamps=tuple(timestamps), values=tuple(values), symbol="BTCUSDT", timeframe="1h"
        )
        ctx = SeriesContext(close=close_series)

        with pytest.raises(ValueError, match="Bollinger Bands period and std_dev must be positive"):
            bbands(ctx, period=0)
        with pytest.raises(ValueError, match="Bollinger Bands period and std_dev must be positive"):
            bbands(ctx, std_dev=0)

    def test_bbands_different_std_dev(self):
        """Test BBands with different standard deviation values."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 26)]
        values = [Decimal(str(100 + i)) for i in range(25)]
        close_series = Series[Price](
            timestamps=tuple(timestamps), values=tuple(values), symbol="BTCUSDT", timeframe="1h"
        )
        ctx = SeriesContext(close=close_series)

        upper1, middle1, lower1 = bbands(ctx, period=20, std_dev=1.0)
        # Use default std_dev=2.0
        upper2, middle2, lower2 = bbands(ctx, period=20)
        upper3, middle3, lower3 = bbands(ctx, period=20, std_dev=3.0)

        # Middle bands should be identical
        for i in range(len(middle1.values)):
            m1, m2, m3 = middle1.values[i], middle2.values[i], middle3.values[i]
            if isinstance(m1, Decimal) and m1.is_nan():
                assert m2.is_nan() and m3.is_nan()
            else:
                assert m1 == m2 == m3

        # Higher std_dev should result in wider bands
        for i in range(len(upper3.timestamps)):
            if upper3.availability_mask[i]:
                assert float(upper3.values[i]) > float(upper1.values[i])
                assert float(lower3.values[i]) < float(lower1.values[i])
