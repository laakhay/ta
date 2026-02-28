"""Tests for WMA indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.trend.wma import wma
from laakhay.ta.registry.models import SeriesContext


class TestWMAIndicator:
    """Test Weighted Moving Average indicator."""

    def test_wma_basic_calculation(self):
        """Test basic WMA calculation."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 6)]
        values = [Decimal("10"), Decimal("20"), Decimal("30"), Decimal("40"), Decimal("50")]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)
        result = wma(ctx, period=3)

        # For period=3, WMA = (1*P1 + 2*P2 + 3*P3) / (1+2+3)
        # First two values should be 0 or masked (we use _with_window_mask in rolling_wma)
        assert result.values[0].is_nan()
        assert result.values[1].is_nan()

        # Third value (index 2): (1*10 + 2*20 + 3*30) / 6 = (10 + 40 + 90) / 6 = 140 / 6 = 23.333...
        expected_third = Decimal("140") / Decimal("6")
        assert abs(result.values[2] - expected_third) < Decimal("0.0001")

        # Fourth value (index 3): (1*20 + 2*30 + 3*40) / 6 = (20 + 60 + 120) / 6 = 200 / 6 = 33.333...
        expected_fourth = Decimal("200") / Decimal("6")
        assert abs(result.values[3] - expected_fourth) < Decimal("0.0001")

    def test_wma_metadata_inheritance(self):
        """Test that WMA preserves input series metadata."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 2, tzinfo=UTC)]
        values = [Decimal("100"), Decimal("101")]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h",
        )

        ctx = SeriesContext(close=close_series)
        result = wma(ctx, period=2)

        assert result.symbol == "ETHUSDT"
        assert result.timeframe == "4h"

    def test_wma_invalid_period(self):
        """Test WMA with invalid period."""
        close_series = Series[Price](
            timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
            values=(Decimal("100"),),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        ctx = SeriesContext(close=close_series)

        with pytest.raises(ValueError, match="Period must be positive"):
            wma(ctx, period=0)
