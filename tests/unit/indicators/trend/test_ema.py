"""Tests for EMA indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.trend.ema import ema
from laakhay.ta.registry.models import SeriesContext


class TestEMAIndicator:
    """Test Exponential Moving Average indicator."""

    def test_ema_basic_calculation(self):
        """Test basic EMA calculation with valid data."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
            datetime(2024, 1, 5, tzinfo=UTC),
        ]
        values = [Decimal('100'), Decimal('101'), Decimal('102'), Decimal('103'), Decimal('104')]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(close=close_series)
        result = ema(ctx, period=3)

        # EMA should have same length as input
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 5
        assert len(result.values) == 5
        assert result.timestamps == tuple(timestamps)

        # First value should be the same as input
        assert result.values[0] == values[0]

        # Subsequent values should be smoothed
        assert result.values[1] != values[1]  # Should be smoothed
        assert result.values[2] != values[2]  # Should be smoothed

    def test_ema_period_one(self):
        """Test EMA with period=1 (should return same values)."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 2, tzinfo=UTC)]
        values = [Decimal('100'), Decimal('101')]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(close=close_series)
        result = ema(ctx, period=1)

        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert result.timestamps == tuple(timestamps)
        assert result.values == tuple(values)

    def test_ema_empty_series(self):
        """Test EMA with empty input series."""
        close_series = Series[Price](
            timestamps=(),
            values=(),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(close=close_series)
        result = ema(ctx, period=3)

        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 0
        assert len(result.values) == 0

    def test_ema_single_value(self):
        """Test EMA with single value."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal('100')]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(close=close_series)
        result = ema(ctx, period=3)

        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert result.timestamps == tuple(timestamps)
        assert result.values == tuple(values)

    def test_ema_default_period(self):
        """Test EMA with default period parameter."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 26)]  # 25 days
        values = [Decimal(str(100 + i)) for i in range(25)]  # 100, 101, ..., 124

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(close=close_series)
        result = ema(ctx)  # Use default period=20

        assert len(result.timestamps) == 25
        assert len(result.values) == 25
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"

    def test_ema_invalid_period(self):
        """Test EMA with invalid period."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal('100')]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(close=close_series)

        with pytest.raises(ValueError, match="Period must be positive"):
            ema(ctx, period=0)

        with pytest.raises(ValueError, match="Period must be positive"):
            ema(ctx, period=-1)

    def test_ema_metadata_inheritance(self):
        """Test that EMA preserves input series metadata."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 2, tzinfo=UTC)]
        values = [Decimal('100'), Decimal('101')]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h"
        )

        ctx = SeriesContext(close=close_series)
        result = ema(ctx, period=2)

        assert result.symbol == "ETHUSDT"
        assert result.timeframe == "4h"

    def test_ema_smoothing_factor(self):
        """Test that EMA uses correct smoothing factor."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 2, tzinfo=UTC)]
        values = [Decimal('100'), Decimal('110')]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(close=close_series)
        result = ema(ctx, period=2)

        # For period=2, alpha = 2/(2+1) = 2/3
        # EMA[1] = 100 (first value)
        # EMA[2] = (2/3) * 110 + (1/3) * 100 = 73.33 + 33.33 = 106.67
        expected_second_value = Decimal('2') / Decimal('3') * Decimal('110') + Decimal('1') / Decimal('3') * Decimal('100')

        assert result.values[0] == Decimal('100')
        assert abs(float(result.values[1]) - float(expected_second_value)) < 0.01
