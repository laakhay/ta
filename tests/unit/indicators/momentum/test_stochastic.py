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
        low_values = [Decimal(str(99 + i)) for i in range(16)]   # 99, 100, ..., 114
        close_values = [Decimal(str(99.5 + i)) for i in range(16)]  # 99.5, 100.5, ..., 114.5

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(high_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(low_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        k_series, d_series = stochastic(ctx, k_period=14, d_period=3)

        assert k_series.symbol == "BTCUSDT"
        assert d_series.symbol == "BTCUSDT"
        assert k_series.timeframe == "1h"
        assert d_series.timeframe == "1h"

        # K should have length 3 (16 - 14 + 1)
        assert len(k_series.timestamps) == 3
        assert len(k_series.values) == 3

        # D should have length 1 (3 - 3 + 1)
        assert len(d_series.timestamps) == 1
        assert len(d_series.values) == 1

    def test_stochastic_empty_series(self):
        """Test Stochastic with empty input series."""
        empty_series = Series[Price](
            timestamps=(),
            values=(),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(high=empty_series, low=empty_series, close=empty_series)
        k_series, d_series = stochastic(ctx)

        assert k_series.symbol == "BTCUSDT"
        assert d_series.symbol == "BTCUSDT"
        assert len(k_series.timestamps) == 0
        assert len(d_series.timestamps) == 0

    def test_stochastic_insufficient_data(self):
        """Test Stochastic with insufficient data for k_period."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 11)]  # 10 days
        values = [Decimal(str(100 + i)) for i in range(10)]  # 100, 101, ..., 109

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        k_series, d_series = stochastic(ctx, k_period=14)

        # Should return empty series when insufficient data
        assert len(k_series.timestamps) == 0
        assert len(d_series.timestamps) == 0

    def test_stochastic_missing_series(self):
        """Test Stochastic with missing required series."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal('100')]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        # Test missing high
        ctx = SeriesContext(low=close_series, close=close_series)
        with pytest.raises(ValueError, match="Stochastic requires series: .* missing: .*high.*"):
            stochastic(ctx)

        # Test missing low
        ctx = SeriesContext(high=close_series, close=close_series)
        with pytest.raises(ValueError, match="Stochastic requires series: .* missing: .*low.*"):
            stochastic(ctx)

        # Test missing close
        ctx = SeriesContext(high=close_series, low=close_series)
        with pytest.raises(ValueError, match="Stochastic requires series: .* missing: .*close.*"):
            stochastic(ctx)

    def test_stochastic_different_lengths(self):
        """Test Stochastic with different length series."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]
        values = [Decimal(str(100 + i)) for i in range(16)]
        short_values = [Decimal(str(100 + i)) for i in range(10)]  # Different length

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps[:10]),
            values=tuple(short_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        with pytest.raises(ValueError, match="All series must have the same length"):
            stochastic(ctx)

    def test_stochastic_invalid_periods(self):
        """Test Stochastic with invalid period parameters."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]
        values = [Decimal(str(100 + i)) for i in range(16)]

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)

        with pytest.raises(ValueError, match="Stochastic periods must be positive"):
            stochastic(ctx, k_period=0, d_period=3)

        with pytest.raises(ValueError, match="Stochastic periods must be positive"):
            stochastic(ctx, k_period=14, d_period=0)

        with pytest.raises(ValueError, match="Stochastic periods must be positive"):
            stochastic(ctx, k_period=-1, d_period=3)

    def test_stochastic_default_parameters(self):
        """Test Stochastic with default parameters."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]  # 16 days
        high_values = [Decimal(str(100 + i)) for i in range(16)]
        low_values = [Decimal(str(99 + i)) for i in range(16)]
        close_values = [Decimal(str(99.5 + i)) for i in range(16)]

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(high_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(low_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        k_series, d_series = stochastic(ctx)  # Use defaults: k_period=14, d_period=3

        assert len(k_series.timestamps) == 3  # 16 - 14 + 1
        assert len(d_series.timestamps) == 1  # 3 - 3 + 1
        assert k_series.symbol == "BTCUSDT"
        assert d_series.symbol == "BTCUSDT"

    def test_stochastic_percent_k_range(self):
        """Test that %K values are between 0 and 100."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]  # 16 days
        high_values = [Decimal(str(100 + i)) for i in range(16)]
        low_values = [Decimal(str(99 + i)) for i in range(16)]
        close_values = [Decimal(str(99.5 + i)) for i in range(16)]

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(high_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(low_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        k_series, d_series = stochastic(ctx, k_period=14, d_period=3)

        # %K should be between 0 and 100
        for value in k_series.values:
            assert 0 <= float(value) <= 100

        # %D should also be between 0 and 100 (SMA of %K)
        for value in d_series.values:
            assert 0 <= float(value) <= 100

    def test_stochastic_metadata_inheritance(self):
        """Test that Stochastic preserves input series metadata."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]
        high_values = [Decimal(str(100 + i)) for i in range(16)]
        low_values = [Decimal(str(99 + i)) for i in range(16)]
        close_values = [Decimal(str(99.5 + i)) for i in range(16)]

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(high_values),
            symbol="ETHUSDT",
            timeframe="4h"
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(low_values),
            symbol="ETHUSDT",
            timeframe="4h"
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="ETHUSDT",
            timeframe="4h"
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        k_series, d_series = stochastic(ctx)

        assert k_series.symbol == "ETHUSDT"
        assert d_series.symbol == "ETHUSDT"
        assert k_series.timeframe == "4h"
        assert d_series.timeframe == "4h"

    def test_stochastic_identical_high_low(self):
        """Test Stochastic when high equals low (should result in %K = 50)."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 17)]  # 16 days
        values = [Decimal('100')] * 16  # All same values

        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )

        ctx = SeriesContext(high=high_series, low=low_series, close=close_series)
        k_series, d_series = stochastic(ctx, k_period=14, d_period=3)

        # When high = low = close, %K should be 50
        for value in k_series.values:
            assert abs(float(value) - 50.0) < 0.01
