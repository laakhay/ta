"""Tests for Elder Ray Index."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.trend.elder_ray import elder_ray
from laakhay.ta.registry.models import SeriesContext


class TestElderRayIndicator:
    """Test Elder Ray Index."""

    def test_elder_ray_basic_calculation(self):
        """Test basic Elder Ray calculation."""
        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        timestamps = [start_date + timedelta(days=i) for i in range(20)]
        highs = [110 + i for i in range(20)]
        lows = [90 + i for i in range(20)]
        closes = [100 + i for i in range(20)]

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

        bull, bear = elder_ray(ctx, period=13)

        assert len(bull.values) == 20
        assert len(bear.values) == 20
        assert bull.timestamps == tuple(timestamps)

    def test_elder_ray_invalid_params(self):
        """Test Elder Ray with invalid parameters."""
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
        with pytest.raises(ValueError, match="Elder Ray period must be positive"):
            elder_ray(ctx, period=0)
