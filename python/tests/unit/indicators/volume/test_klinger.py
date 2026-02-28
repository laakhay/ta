"""Tests for Klinger Oscillator indicator."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.volume.klinger import klinger
from laakhay.ta.registry.models import SeriesContext


class TestKlingerIndicator:
    """Test Klinger Oscillator."""

    def test_klinger_basic_calculation(self):
        """Test basic Klinger calculation."""
        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        timestamps = [start_date + timedelta(days=i) for i in range(60)]
        highs = [110 + i for i in range(60)]
        lows = [90 + i for i in range(60)]
        closes = [100 + i for i in range(60)]
        volumes = [1000 for _ in range(60)]

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

        kl, sig = klinger(ctx, fast_period=34, slow_period=55, signal_period=13)

        assert len(kl.values) == 60
        assert len(sig.values) == 60
        assert kl.timestamps == tuple(timestamps)

    def test_klinger_invalid_params(self):
        """Test Klinger with invalid parameters."""
        ctx = SeriesContext(
            close=Series[Price](
                timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
                values=(Decimal("95"),),
                symbol="BTCUSDT",
                timeframe="1h",
            ),
        )
        with pytest.raises(ValueError, match="Klinger periods must be positive"):
            klinger(ctx, fast_period=0)
