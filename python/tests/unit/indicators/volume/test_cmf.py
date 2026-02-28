"""Tests for Chaikin Money Flow (CMF) indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.volume.cmf import cmf
from laakhay.ta.registry.models import SeriesContext


class TestCMFIndicator:
    """Test Chaikin Money Flow (CMF) indicator."""

    def test_cmf_basic_logic(self):
        """Test basic CMF calculation."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 21)]
        highs = [100 + i for i in range(20)]
        lows = [90 + i for i in range(20)]
        closes = [98 + i for i in range(20)]  # Close near high
        volumes = [1000 for _ in range(20)]

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
            volume=Series[Price](
                timestamps=tuple(timestamps),
                values=tuple(Decimal(str(v)) for v in volumes),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )

        result = cmf(ctx, period=10)

        assert len(result.values) == 20
        # Since close is consistently near high, CMF should be positive
        assert result.values[-1] > 0

    def test_cmf_invalid_period(self):
        """Test CMF with invalid parameters."""
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
            volume=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("1000"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )
        with pytest.raises(ValueError, match="CMF period must be positive"):
            cmf(ctx, period=0)
