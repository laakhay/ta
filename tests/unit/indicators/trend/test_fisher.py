"""Tests for Fisher Transform indicator."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.trend.fisher import fisher
from laakhay.ta.registry.models import SeriesContext


class TestFisherIndicator:
    """Test Fisher Transform indicator."""

    def test_fisher_basic_calculation(self):
        """Test basic Fisher Transform calculation."""
        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        timestamps = [start_date + timedelta(days=i) for i in range(20)]
        highs = [110 + i for i in range(20)]
        lows = [90 + i for i in range(20)]

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

        fish, signal = fisher(ctx, period=9)

        assert len(fish.values) == 20
        assert len(signal.values) == 20
        assert fish.timestamps == tuple(timestamps)

    def test_fisher_invalid_params(self):
        """Test Fisher with invalid parameters."""
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
        with pytest.raises(ValueError, match="Fisher period must be positive"):
            fisher(ctx, period=0)
