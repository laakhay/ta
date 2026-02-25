"""Tests for Parabolic SAR indicator."""

from datetime import UTC, datetime
from decimal import Decimal

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.trend.psar import psar
from laakhay.ta.registry.models import SeriesContext


class TestPSARIndicator:
    """Test Parabolic SAR indicator."""

    def test_psar_basic_logic(self):
        """Test basic PSAR logic (trend reversal)."""
        # Create a series that starts rising then falls
        timestamps = [datetime(2024, 1, i, tzinfo=UTC) for i in range(1, 11)]
        highs = [100, 105, 110, 115, 120, 115, 110, 105, 100, 95]
        lows = [95, 100, 105, 110, 115, 110, 105, 100, 95, 90]
        closes = [98, 103, 108, 113, 118, 113, 108, 103, 98, 93]

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

        sar, direction = psar(ctx)

        # Initial trend should be long (1)
        assert direction.values[0] == Decimal("1")

        # It should eventually reverse to short (-1) as price drops below SAR
        assert Decimal("-1") in direction.values

    def test_psar_empty_series(self):
        """Test PSAR with empty input."""
        ctx = SeriesContext(
            high=Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h"),
            low=Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h"),
            close=Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h"),
        )
        sar, direction = psar(ctx)
        assert len(sar.values) == 0
        assert len(direction.values) == 0
