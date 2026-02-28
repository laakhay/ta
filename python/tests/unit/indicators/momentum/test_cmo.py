"""Tests for CMO indicator."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.momentum.cmo import cmo
from laakhay.ta.registry.models import SeriesContext


class TestCMOIndicator:
    """Test CMO indicator."""

    def test_cmo_basic_calculation(self):
        """Test basic CMO calculation."""
        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        timestamps = [start_date + timedelta(days=i) for i in range(20)]
        closes = [100 + i for i in range(20)]

        ctx = SeriesContext(
            close=Series[Price](
                timestamps=tuple(timestamps),
                values=tuple(Decimal(str(v)) for v in closes),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )

        result = cmo(ctx, period=14)

        assert len(result.values) == 20
        assert result.timestamps == tuple(timestamps)

    def test_cmo_invalid_params(self):
        """Test CMO with invalid parameters."""
        ctx = SeriesContext(
            close=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("95"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )
        with pytest.raises(ValueError, match="CMO period must be positive"):
            cmo(ctx, period=0)
