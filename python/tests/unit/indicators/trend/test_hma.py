"""Tests for HMA indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.trend.hma import hma
from laakhay.ta.registry.models import SeriesContext


class TestHMAIndicator:
    """Test Hull Moving Average indicator."""

    def test_hma_basic_calculation(self):
        """Test basic HMA directional correctness."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 21)]
        # Ascending values
        values = [Decimal(str(i * 10)) for i in range(1, 21)]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        result = hma(ctx, period=10)

        # HMA should be calculated for later values
        assert len(result.values) == 20
        # For ascending series, HMA should also be ascending and close to the latest values
        assert result.values[-1] > result.values[-2]

    def test_hma_invalid_period(self):
        """Test HMA with invalid period."""
        close_series = Series[Price](
            timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
            values=(Decimal("100"),),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        ctx = SeriesContext(close=close_series)

        with pytest.raises(ValueError, match="HMA period must be positive"):
            hma(ctx, period=0)
