"""Tests for Coppock Curve indicator."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.momentum.coppock import coppock
from laakhay.ta.registry.models import SeriesContext


class TestCoppockIndicator:
    """Test Coppock Curve indicator."""

    def test_coppock_basic_calculation(self):
        """Test basic Coppock Curve calculation."""
        # Need enough bars for ROC (14) + WMA (10)
        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        timestamps = [start_date + timedelta(days=i) for i in range(40)]
        closes = [100 + i for i in range(40)]

        ctx = SeriesContext(
            close=Series[Price](
                timestamps=tuple(timestamps),
                values=tuple(Decimal(str(v)) for v in closes),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )

        result = coppock(ctx, wma_period=10, fast_roc=11, slow_roc=14)

        assert len(result.values) == 40
        assert result.timestamps == tuple(timestamps)

    def test_coppock_invalid_params(self):
        """Test Coppock with invalid parameters."""
        ctx = SeriesContext(
            close=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("95"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )
        with pytest.raises(ValueError, match="Coppock periods must be positive"):
            coppock(ctx, wma_period=0)
