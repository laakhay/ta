"""Tests for basic technical indicators."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.registry.models import SeriesContext
from laakhay.ta.indicators.basic import sma


class TestSMAIndicator:
    """Test Simple Moving Average indicator."""

    def test_sma_basic_calculation(self):
        """Test basic SMA calculation with valid data."""
        # Create test data: prices [100, 101, 102, 103, 104]
        timestamps = [
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 1, 2, tzinfo=timezone.utc),
            datetime(2024, 1, 3, tzinfo=timezone.utc),
            datetime(2024, 1, 4, tzinfo=timezone.utc),
            datetime(2024, 1, 5, tzinfo=timezone.utc),
        ]
        values = [Decimal('100'), Decimal('101'), Decimal('102'), Decimal('103'), Decimal('104')]
        
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(close=close_series)
        result = sma(ctx, period=3)
        
        # SMA(3) should start from index 2: (100+101+102)/3, (101+102+103)/3, (102+103+104)/3
        expected_values = [Decimal('101'), Decimal('102'), Decimal('103')]
        expected_timestamps = timestamps[2:]
        
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 3
        assert len(result.values) == 3
        assert result.timestamps == tuple(expected_timestamps)
        assert result.values == tuple(expected_values)

    def test_sma_period_larger_than_data(self):
        """Test SMA with period larger than available data."""
        timestamps = [datetime(2024, 1, 1, tzinfo=timezone.utc)]
        values = [Decimal('100')]
        
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(close=close_series)
        result = sma(ctx, period=5)
        
        # Should return empty series when period > data length
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 0
        assert len(result.values) == 0

    def test_sma_single_value(self):
        """Test SMA with period=1 (should return the same data)."""
        timestamps = [datetime(2024, 1, 1, tzinfo=timezone.utc)]
        values = [Decimal('100')]
        
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(close=close_series)
        result = sma(ctx, period=1)
        
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert result.timestamps == tuple(timestamps)
        assert result.values == tuple(values)

    def test_sma_empty_series(self):
        """Test SMA with empty input series."""
        close_series = Series[Price](
            timestamps=(),
            values=(),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(close=close_series)
        result = sma(ctx, period=3)
        
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 0
        assert len(result.values) == 0

    def test_sma_default_period(self):
        """Test SMA with default period parameter."""
        timestamps = [datetime(2024, 1, i, tzinfo=timezone.utc) for i in range(1, 26)]  # 25 days
        values = [Decimal(str(100 + i)) for i in range(25)]  # 100, 101, ..., 124
        
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(close=close_series)
        result = sma(ctx)  # Use default period=20
        
        # Should have 6 values (25 - 20 + 1)
        assert len(result.timestamps) == 6
        assert len(result.values) == 6
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"

    def test_sma_metadata_inheritance(self):
        """Test that SMA preserves input series metadata."""
        timestamps = [datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 2, tzinfo=timezone.utc)]
        values = [Decimal('100'), Decimal('101')]
        
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h"
        )
        
        ctx = SeriesContext(close=close_series)
        result = sma(ctx, period=2)
        
        assert result.symbol == "ETHUSDT"
        assert result.timeframe == "4h"
