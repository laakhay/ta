"""Tests for Donchian Channels indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.volatility.donchian import donchian
from laakhay.ta.registry.models import SeriesContext


class TestDonchianIndicator:
    """Test Donchian Channels indicator."""

    def test_donchian_basic_calculation(self):
        """Test basic Donchian calculation."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 6)]
        highs = [100, 110, 105, 120, 115]
        lows = [90, 95, 85, 100, 95]

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
        )

        upper, lower, middle = donchian(ctx, period=3)

        # At index 2 (window: 100, 110, 105)
        assert upper.values[2] == Decimal("110")
        assert lower.values[2] == Decimal("85")
        assert middle.values[2] == (Decimal("110") + Decimal("85")) / Decimal("2")

        # At index 3 (window: 110, 105, 120)
        assert upper.values[3] == Decimal("120")
        assert lower.values[3] == Decimal("85")

    def test_donchian_invalid_period(self):
        """Test Donchian with invalid period."""
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
        )
        with pytest.raises(ValueError, match="Donchian period must be positive"):
            donchian(ctx, period=0)
