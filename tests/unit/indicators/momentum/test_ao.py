"""Tests for Awesome Oscillator (AO) indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.momentum.ao import ao
from laakhay.ta.registry.models import SeriesContext


class TestAOIndicator:
    """Test Awesome Oscillator indicator."""

    def test_ao_basic_calculation(self):
        """Test basic AO calculation."""
        # 40 bars to cover slow_period=34
        timestamps = [
            datetime(2024, 1, i, tzinfo=UTC) if i <= 31 else datetime(2024, 2, i - 31, tzinfo=UTC) for i in range(1, 41)
        ]
        highs = [100 + i for i in range(40)]
        lows = [90 + i for i in range(40)]

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

        result = ao(ctx, fast_period=5, slow_period=34)

        # Latest value should be calculated
        assert len(result.values) == 40
        assert result.values[-1] != Decimal(0)

    def test_ao_invalid_period(self):
        """Test AO with invalid period."""
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
        with pytest.raises(ValueError, match="Periods must be positive"):
            ao(ctx, fast_period=0)
