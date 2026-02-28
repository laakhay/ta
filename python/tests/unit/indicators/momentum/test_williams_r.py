"""Tests for Williams %R indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.momentum.williams_r import williams_r
from laakhay.ta.registry.models import SeriesContext


class TestWilliamsRIndicator:
    """Test Williams %R indicator."""

    def test_williams_r_basic_logic(self):
        """Test basic Williams %R calculation."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 6)]
        highs = [100, 110, 105, 120, 115]
        lows = [90, 95, 85, 100, 95]
        closes = [98, 103, 108, 113, 118]

        ctx = SeriesContext(
            high=Series[Price](
                timestamps=tuple(timestamps),
                values=tuple(Decimal(str(v)) for v in highs),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
            low=Series[Price](
                timestamps=tuple(timestamps),
                values=tuple(Decimal(str(v)) for v in lows),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
            close=Series[Price](
                timestamps=tuple(timestamps),
                values=tuple(Decimal(str(v)) for v in closes),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )

        result = williams_r(ctx, period=3)

        # Period 3 at index 2 (H: 100, 110, 105; L: 90, 95, 85; C: 108)
        # HH = 110, LL = 85
        # %R = (110 - 108) / (110 - 85) * -100 = 2 / 25 * -100 = 0.08 * -100 = -8
        assert abs(result.values[2] - Decimal("-8")) < Decimal("0.0001")

    def test_williams_r_invalid_period(self):
        """Test Williams %R with invalid parameters."""
        ctx = SeriesContext(
            high=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("100"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
            low=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("90"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
            close=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("95"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )
        with pytest.raises(ValueError, match="Williams %R period must be positive"):
            williams_r(ctx, period=0)
