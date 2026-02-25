"""Tests for Supertrend indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.trend.supertrend import supertrend
from laakhay.ta.registry.models import SeriesContext


class TestSupertrendIndicator:
    """Test Supertrend indicator."""

    def test_supertrend_basic_calculation(self):
        """Test basic Supertrend calculation and directional logic."""
        # Need enough bars for ATR smoothing
        timestamps = [
            datetime(2024, 1, i, tzinfo=UTC) if i <= 31 else datetime(2024, 2, i - 31, tzinfo=UTC) for i in range(1, 31)
        ]
        highs = [100 + i for i in range(30)]
        lows = [95 + i for i in range(30)]
        closes = [98 + i for i in range(30)]

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

        # Period 10, Multiplier 3
        band, direction = supertrend(ctx, period=10, multiplier=3.0)

        # In a purely rising market, direction should eventually be 1
        assert direction.values[-1] == Decimal("1")
        # Band should be below close
        assert band.values[-1] < ctx.close.values[-1]

    def test_supertrend_invalid_period(self):
        """Test Supertrend with invalid parameters."""
        ctx = SeriesContext(
            high=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("100"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
            low=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("95"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
            close=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("98"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )
        with pytest.raises(ValueError, match="Supertrend period must be positive"):
            supertrend(ctx, period=0)
