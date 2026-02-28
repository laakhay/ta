"""Tests for CCI indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.momentum.cci import cci
from laakhay.ta.registry.models import SeriesContext


class TestCCIIndicator:
    """Test Commodity Channel Index (CCI) indicator."""

    def test_cci_basic_calculation(self):
        """Test basic CCI calculation."""
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

        result = cci(ctx, period=14)

        assert len(result.values) == 20
        # In a stable trend, CCI should eventually reflect the deviation.
        assert result.values[-1] != Decimal(0)

    def test_cci_invalid_period(self):
        """Test CCI with invalid parameters."""
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
        with pytest.raises(ValueError, match="CCI period must be positive"):
            cci(ctx, period=0)
