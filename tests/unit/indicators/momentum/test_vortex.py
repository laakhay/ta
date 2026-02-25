"""Tests for Vortex Indicator."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.momentum.vortex import vortex
from laakhay.ta.registry.models import SeriesContext


class TestVortexIndicator:
    """Test Vortex Indicator."""

    def test_vortex_basic_calculation(self):
        """Test basic Vortex calculation and alignment."""
        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        timestamps = [start_date + timedelta(days=i) for i in range(20)]
        highs = [100 + i for i in range(20)]
        lows = [90 + i for i in range(20)]
        closes = [95 + i for i in range(20)]

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

        vip, vim = vortex(ctx, period=10)

        assert len(vip.values) == 20
        assert len(vim.values) == 20
        assert vip.timestamps == tuple(timestamps)

    def test_vortex_invalid_params(self):
        """Test Vortex with invalid parameters."""
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
        with pytest.raises(ValueError, match="Vortex period must be positive"):
            vortex(ctx, period=0)
