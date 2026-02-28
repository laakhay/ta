"""Tests for MFI indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.momentum.mfi import mfi
from laakhay.ta.registry.models import SeriesContext


class TestMFIIndicator:
    """Test Money Flow Index indicator."""

    def test_mfi_basic_calculation(self):
        """Test basic MFI calculation."""
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 6)]
        highs = [100, 105, 110, 115, 120]
        lows = [95, 100, 105, 110, 115]
        closes = [98, 103, 108, 113, 118]
        volumes = [1000, 1000, 1000, 1000, 1000]

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

        # Period 3
        result = mfi(ctx, period=3)

        # MFI should be 100 as price is always rising in this sample
        # Note: Index 3 (4th value) is the first with a valid 3-period window if we count deltas
        # Bars: 1, 2, 3, 4, 5
        # TP diffs: (2-1), (3-2), (4-3), (5-4) -> all positive
        assert result.values[-1] == Decimal("100")

    def test_mfi_invalid_period(self):
        """Test MFI with invalid period."""
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
            volume=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("1000"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )
        with pytest.raises(ValueError, match="MFI period must be positive"):
            mfi(ctx, period=0)
