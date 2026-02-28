"""Tests for ROC indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.momentum.roc import roc
from laakhay.ta.registry.models import SeriesContext


class TestROCIndicator:
    """Test Rate of Change (ROC) indicator."""

    def test_roc_basic_calculation(self):
        """Test basic ROC calculation."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 4)]
        values = [Decimal("100"), Decimal("110"), Decimal("121")]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series)

        # ROC(1) = (C - C_prev)/C_prev * 100
        result = roc(ctx, period=1)

        # Index 1: (110 - 100)/100 * 100 = 10
        assert result.values[1] == Decimal("10")

        # Index 2: (121 - 110)/110 * 100 = 0.1 * 100 = 10
        assert result.values[2] == Decimal("10")

    def test_roc_invalid_period(self):
        """Test ROC with invalid parameters."""
        close_series = Series[Price](
            timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
            values=(Decimal("100"),),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        ctx = SeriesContext(close=close_series)
        with pytest.raises(ValueError, match="ROC period must be positive"):
            roc(ctx, period=0)
