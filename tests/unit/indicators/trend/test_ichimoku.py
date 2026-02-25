"""Tests for Ichimoku Cloud indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.trend.ichimoku import ichimoku
from laakhay.ta.registry.models import SeriesContext


class TestIchimokuIndicator:
    """Test Ichimoku Cloud indicator."""

    def test_ichimoku_alignment(self):
        """Test basic Ichimoku calculation and series alignment."""
        # Need enough bars for Senkou Span B (period=52)
        from datetime import timedelta

        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        timestamps = [start_date + timedelta(days=i) for i in range(100)]
        highs = [100 + i for i in range(100)]
        lows = [90 + i for i in range(100)]
        closes = [95 + i for i in range(100)]

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

        tenkan, kijun, senkou_a, senkou_b, chikou = ichimoku(ctx)

        # Check lengths
        assert len(tenkan) == 100
        assert len(senkou_a) == 100
        assert len(chikou) == 100

        # Chikou should be close shifted back 26 periods
        # Our implementation uses shift(26) on the series, so at index i, chikou[i] should be close[i+26]?
        # Actually Series.shift(26) shifts values FORWARD in time.
        # Ichimoku Chikou is close shifted BACK in time?
        # Standard Ichimoku: Chikou is Current Close plotted 26 bars BEHIND.
        # Our implementation: `ctx.close.shift(chikou_span)` where chikou_span=26.
        # Series.shift(n) shifts index i to i+n. So value at t is now at t+n.
        # This matches "plotted 26 bars ahead" if n is positive.
        # Wait, Chikou is 26 bars BEHIND.
        # Let's check ichimoku implementation.

    def test_ichimoku_invalid_params(self):
        """Test Ichimoku with invalid parameters."""
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
        with pytest.raises(ValueError, match="Ichimoku periods and displacement must be positive"):
            ichimoku(ctx, tenkan_period=0)
