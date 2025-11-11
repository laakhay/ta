"""Tests for ATR indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.volatility.atr import atr
from laakhay.ta.registry.models import SeriesContext


class TestATRIndicator:
    """Test Average True Range indicator."""

    def test_atr_basic_calculation(self):
        """Test basic ATR calculation with valid data."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
        ]
        high_values = [Decimal("101"), Decimal("102"), Decimal("103"), Decimal("104")]
        low_values = [Decimal("99"), Decimal("100"), Decimal("101"), Decimal("102")]
        close_values = [Decimal("100"), Decimal("101"), Decimal("102"), Decimal("103")]

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(high_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(low_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        result = atr(ctx, period=3)

        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 2  # 4 - 3 + 1
        assert len(result.values) == 2

    def test_atr_empty_series(self):
        """Test ATR with empty input series."""
        empty_series = Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h")

        ctx = SeriesContext(high=empty_series, low=empty_series, close=empty_series)
        result = atr(ctx)

        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 0
        assert len(result.values) == 0

    def test_atr_insufficient_data(self):
        """Test ATR with insufficient data for period."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal("100")]

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        result = atr(ctx, period=3)

        # Should return empty series when insufficient data
        assert len(result.timestamps) == 0
        assert len(result.values) == 0

    def test_atr_single_value(self):
        """Test ATR with single value (should return empty)."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal("100")]

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        result = atr(ctx, period=2)

        # Need at least 2 values for true range calculation
        assert len(result.timestamps) == 0
        assert len(result.values) == 0

    def test_atr_missing_series(self):
        """Test ATR with missing required series."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal("100")]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        # Test missing high
        ctx = SeriesContext(low=close_series, close=close_series)
        with pytest.raises(ValueError, match="True Range requires series: .*high.*low.*close.*"):
            atr(ctx)

        # Test missing low
        ctx = SeriesContext(high=close_series, close=close_series)
        with pytest.raises(ValueError, match="True Range requires series: .*high.*low.*close.*"):
            atr(ctx)

        # Test missing close
        ctx = SeriesContext(high=close_series, low=close_series)
        with pytest.raises(ValueError, match="True Range requires series: .*high.*low.*close.*"):
            atr(ctx)

    def test_atr_different_lengths(self):
        """Test ATR with different length series."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        values = [Decimal("100"), Decimal("101")]
        short_values = [Decimal("100")]  # Different length

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps[:1]),
            values=tuple(short_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        with pytest.raises(ValueError, match="All series must have the same length"):
            atr(ctx)

    def test_atr_invalid_period(self):
        """Test ATR with invalid period."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        values = [Decimal("100"), Decimal("101")]

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)

        with pytest.raises(ValueError, match="ATR period must be positive"):
            atr(ctx, period=0)

        with pytest.raises(ValueError, match="ATR period must be positive"):
            atr(ctx, period=-1)

    def test_atr_default_period(self):
        """Test ATR with default period parameter."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]  # 16 days
        values = [Decimal(str(100 + i)) for i in range(16)]  # 100, 101, ..., 115

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        result = atr(ctx)  # Use default period=14

        assert len(result.timestamps) == 3  # 16 - 14 + 1
        assert len(result.values) == 3
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"

    def test_atr_metadata_inheritance(self):
        """Test that ATR preserves input series metadata."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]
        values = [Decimal(str(100 + i)) for i in range(16)]

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h",
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h",
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h",
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        result = atr(ctx)

        assert result.symbol == "ETHUSDT"
        assert result.timeframe == "4h"
