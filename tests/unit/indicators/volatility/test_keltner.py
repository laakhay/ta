"""Tests for Keltner Channels indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.volatility.keltner import keltner
from laakhay.ta.registry.models import SeriesContext


class TestKeltnerIndicator:
    """Test Keltner Channels indicator."""

    def test_keltner_basic_logic(self):
        """Test basic Keltner Channel calculation."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 21)]
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

        upper, mid, lower = keltner(ctx, ema_period=10, atr_period=10, multiplier=2.0)

        assert len(mid.values) == 20
        # In a stable trend, middle band should be between upper and lower
        assert lower.values[-1] < mid.values[-1] < upper.values[-1]

    def test_keltner_invalid_params(self):
        """Test Keltner with invalid parameters."""
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
        with pytest.raises(ValueError, match="Keltner periods must be positive"):
            keltner(ctx, ema_period=0)
