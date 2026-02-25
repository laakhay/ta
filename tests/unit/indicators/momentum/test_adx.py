"""Tests for ADX indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.momentum.adx import adx
from laakhay.ta.registry.models import SeriesContext


class TestADXIndicator:
    """Test Average Directional Index (ADX) indicator."""

    def test_adx_basic_calculation(self):
        """Test basic ADX calculation and direction indicators."""
        # Need enough bars for initialization and smoothing (period=14)
        timestamps = [
            datetime(2024, 1, i, tzinfo=UTC) if i <= 31 else datetime(2024, 2, i - 31, tzinfo=UTC) for i in range(1, 51)
        ]
        highs = [100 + i for i in range(50)]
        lows = [95 + i for i in range(50)]
        closes = [98 + i for i in range(50)]

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

        adx_res, plus_di, minus_di = adx(ctx, period=14)

        # In a purely rising market, +DI should be greater than -DI
        assert plus_di.values[-1] > minus_di.values[-1]
        assert adx_res.values[-1] > 0

    def test_adx_invalid_period(self):
        """Test ADX with invalid period."""
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
        with pytest.raises(ValueError, match="ADX period must be positive"):
            adx(ctx, period=0)
