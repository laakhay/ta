"""Tests for Stochastic Oscillator indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.momentum.stochastic import stochastic
from laakhay.ta.registry.models import SeriesContext


class TestStochasticIndicator:
    """Test Stochastic Oscillator indicator."""

    def test_stochastic_basic_calculation(self):
        """Test basic Stochastic calculation with valid data."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]  # 16 days
        high_values = [Decimal(str(100 + i)) for i in range(16)]  # 100, 101, ..., 115
        low_values = [Decimal(str(99 + i)) for i in range(16)]  # 99, 100, ..., 114
        close_values = [Decimal(str(99.5 + i)) for i in range(16)]  # 99.5, 100.5, ..., 114.5

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
        k_series, d_series = stochastic(ctx, k_period=14, d_period=3)

        assert len(k_series.timestamps) == 16
        assert len(d_series.timestamps) == 16
        # K available from index 13 (warmup=13)
        # D available from index 15 (K warmup=13 + D warmup=2)
        assert k_series.availability_mask.count(True) == 3  # 16 - 14 + 1
        assert d_series.availability_mask.count(True) == 1  # 3 - 3 + 1

    def test_stochastic_empty_series(self):
        """Test Stochastic with empty series."""
        empty = Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h")
        ctx = SeriesContext(high=empty, low=empty, close=empty)
        k, d = stochastic(ctx)
        assert len(k.timestamps) == 0

    def test_stochastic_insufficient_data(self):
        """Test Stochastic with insufficient data."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 11)]
        v = [Decimal("100")] * 10
        series = Series[Price](timestamps=tuple(timestamps), values=tuple(v), symbol="BTCUSDT", timeframe="1h")
        ctx = SeriesContext(high=series, low=series, close=series)
        k, d = stochastic(ctx, k_period=14)
        assert len(k.timestamps) == 10
        assert not any(k.availability_mask)

    def test_stochastic_invalid_periods(self):
        """Test Stochastic with invalid periods."""
        v = [Decimal("100")]
        series = Series[Price](
            timestamps=(datetime(2024, 1, 1, tzinfo=UTC),), values=tuple(v), symbol="BTCUSDT", timeframe="1h"
        )
        ctx = SeriesContext(high=series, low=series, close=series)
        with pytest.raises(ValueError, match="Stochastic periods must be positive"):
            stochastic(ctx, k_period=0)

    def test_stochastic_default_parameters(self):
        """Test Stochastic with default parameters."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]
        v = [Decimal("100")] * 16
        series = Series[Price](timestamps=tuple(timestamps), values=tuple(v), symbol="BTCUSDT", timeframe="1h")
        ctx = SeriesContext(high=series, low=series, close=series)
        k, d = stochastic(ctx)
        assert len(k.timestamps) == 16
        assert len(d.timestamps) == 16
