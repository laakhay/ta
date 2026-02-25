"""Tests for RSI indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.momentum.rsi import rsi
from laakhay.ta.registry.models import SeriesContext


class TestRSIIndicator:
    """Test Relative Strength Index indicator."""

    def test_rsi_basic_calculation(self):
        """Test basic RSI calculation with valid data."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]  # 16 days
        values = [Decimal(str(100 + i)) for i in range(16)]  # 100, 101, ..., 115

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        result = rsi(ctx, period=14)

        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 16
        assert len(result.values) == 16

        # RSI should be between 0 and 100 (where available)
        for i in range(len(result.values)):
            if result.availability_mask[i]:
                assert 0 <= float(result.values[i]) <= 100

    def test_rsi_empty_series(self):
        """Test RSI with empty input series."""
        close_series = Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h")

        ctx = SeriesContext(close=close_series)
        result = rsi(ctx)

        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 0
        assert len(result.values) == 0

    def test_rsi_insufficient_data(self):
        """Test RSI with insufficient data for period."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 11)]  # 10 days
        values = [Decimal(str(100 + i)) for i in range(10)]  # 100, 101, ..., 109

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        result = rsi(ctx, period=14)

        # Should return full length series but all unavailable
        assert len(result.timestamps) == 10
        assert not any(result.availability_mask)

    def test_rsi_single_value(self):
        """Test RSI with single value."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal("100")]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        result = rsi(ctx, period=2)

        assert len(result.timestamps) == 1
        assert not any(result.availability_mask)

    def test_rsi_invalid_period(self):
        """Test RSI with invalid period."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]
        values = [Decimal(str(100 + i)) for i in range(16)]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)

        with pytest.raises(ValueError, match="RSI period must be positive"):
            rsi(ctx, period=0)

    def test_rsi_default_period(self):
        """Test RSI with default period parameter."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]  # 16 days
        values = [Decimal(str(100 + i)) for i in range(16)]  # 100, 101, ..., 115

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        result = rsi(ctx)  # Use default period=14

        assert len(result.timestamps) == 16
        assert result.availability_mask.count(True) == 2  # 16 - 14

    def test_rsi_uptrend(self):
        """Test RSI with uptrending prices (should result in high RSI)."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]  # 16 days
        values = [Decimal(str(100 + i * 2)) for i in range(16)]  # Strong uptrend

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        result = rsi(ctx, period=14)

        # With strong uptrend, RSI should be high (>70) (where available)
        for i in range(len(result.values)):
            if result.availability_mask[i]:
                assert float(result.values[i]) > 70

    def test_rsi_downtrend(self):
        """Test RSI with downtrending prices (should result in low RSI)."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]  # 16 days
        values = [Decimal(str(130 - i * 2)) for i in range(16)]  # Strong downtrend

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        result = rsi(ctx, period=14)

        # With strong downtrend, RSI should be low (<30) (where available)
        for i in range(len(result.values)):
            if result.availability_mask[i]:
                assert float(result.values[i]) < 30
