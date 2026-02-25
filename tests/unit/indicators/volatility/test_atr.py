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
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 5)]  # 4 days
        high = [Decimal("100"), Decimal("102"), Decimal("103"), Decimal("105")]
        low = [Decimal("98"), Decimal("100"), Decimal("101"), Decimal("103")]
        close = [Decimal("99"), Decimal("101"), Decimal("102"), Decimal("104")]

        ctx = SeriesContext(
            high=Series[Price](timestamps=tuple(timestamps), values=tuple(high), symbol="BTCUSDT", timeframe="1h"),
            low=Series[Price](timestamps=tuple(timestamps), values=tuple(low), symbol="BTCUSDT", timeframe="1h"),
            close=Series[Price](timestamps=tuple(timestamps), values=tuple(close), symbol="BTCUSDT", timeframe="1h"),
        )
        result = atr(ctx, period=3)

        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 4
        # period 3 means indices 0,1 are unavailable, 2,3 are available
        assert result.availability_mask == (False, False, True, True)

    def test_atr_empty_series(self):
        """Test ATR with empty input series."""
        empty_series = Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h")
        ctx = SeriesContext(high=empty_series, low=empty_series, close=empty_series)
        result = atr(ctx)
        assert len(result.timestamps) == 0

    def test_atr_insufficient_data(self):
        """Test ATR with insufficient data for period."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        ctx = SeriesContext(
            high=Series[Price](
                timestamps=tuple(timestamps), values=(Decimal("100"),), symbol="BTCUSDT", timeframe="1h"
            ),
            low=Series[Price](timestamps=tuple(timestamps), values=(Decimal("98"),), symbol="BTCUSDT", timeframe="1h"),
            close=Series[Price](
                timestamps=tuple(timestamps), values=(Decimal("99"),), symbol="BTCUSDT", timeframe="1h"
            ),
        )
        result = atr(ctx, period=3)
        assert len(result.timestamps) == 1
        assert not any(result.availability_mask)

    def test_atr_invalid_period(self):
        """Test ATR with invalid period."""
        ctx = SeriesContext(
            high=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("100"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
            low=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("98"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
            close=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("99"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )
        with pytest.raises(ValueError, match="ATR period must be positive"):
            atr(ctx, period=0)

    def test_atr_default_period(self):
        """Test ATR with default period (14)."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]
        values = [Decimal(str(100 + i)) for i in range(16)]
        series = Series[Price](timestamps=tuple(timestamps), values=tuple(values), symbol="BTCUSDT", timeframe="1h")
        ctx = SeriesContext(high=series, low=series, close=series)
        result = atr(ctx)
        assert len(result.timestamps) == 16
        assert result.availability_mask.count(True) == 3  # 16 - 14 + 1
