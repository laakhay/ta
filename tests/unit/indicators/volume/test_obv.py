"""Tests for OBV indicator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price, Qty
from laakhay.ta.indicators.volume.obv import obv
from laakhay.ta.registry.models import SeriesContext


class TestOBVIndicator:
    """Test On-Balance Volume indicator."""

    def test_obv_basic_calculation(self):
        """Test basic OBV calculation with valid data."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
        ]
        close_values = [Decimal("100"), Decimal("101"), Decimal("99"), Decimal("102")]
        volume_values = [
            Decimal("1000"),
            Decimal("1500"),
            Decimal("800"),
            Decimal("1200"),
        ]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        volume_series = Series[Qty](
            timestamps=tuple(timestamps),
            values=tuple(volume_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series, volume=volume_series)
        result = obv(ctx)

        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 4
        assert len(result.values) == 4

        # First value should be first volume
        assert result.values[0] == volume_values[0]

        # Second value: price up (101 > 100), so add volume (1000 + 1500 = 2500)
        assert result.values[1] == Decimal("2500")

        # Third value: price down (99 < 101), so subtract volume (2500 - 800 = 1700)
        assert result.values[2] == Decimal("1700")

        # Fourth value: price up (102 > 99), so add volume (1700 + 1200 = 2900)
        assert result.values[3] == Decimal("2900")

    def test_obv_price_unchanged(self):
        """Test OBV when price remains unchanged."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
        ]
        close_values = [Decimal("100"), Decimal("100"), Decimal("100")]
        volume_values = [Decimal("1000"), Decimal("1500"), Decimal("800")]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        volume_series = Series[Qty](
            timestamps=tuple(timestamps),
            values=tuple(volume_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series, volume=volume_series)
        result = obv(ctx)

        # When price unchanged, add zero (no change to OBV)
        assert result.values[0] == Decimal("1000")
        assert result.values[1] == Decimal("1000")  # 1000 + 0
        assert result.values[2] == Decimal("1000")  # 1000 + 0

    def test_obv_empty_series(self):
        """Test OBV with empty input series."""
        close_series = Series[Price](
            timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h"
        )

        volume_series = Series[Qty](
            timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h"
        )

        ctx = SeriesContext(close=close_series, volume=volume_series)
        result = obv(ctx)

        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 0
        assert len(result.values) == 0

    def test_obv_missing_series(self):
        """Test OBV with missing required series."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal("100")]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        # Test missing volume
        ctx = SeriesContext(close=close_series)
        with pytest.raises(
            ValueError, match="OBV requires both 'close' and 'volume' series"
        ):
            obv(ctx)

        # Test missing close
        volume_series = Series[Qty](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(volume=volume_series)
        with pytest.raises(
            ValueError, match="OBV requires both 'close' and 'volume' series"
        ):
            obv(ctx)

    def test_obv_different_lengths(self):
        """Test OBV with different length series."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        close_values = [Decimal("100"), Decimal("101")]
        volume_values = [Decimal("1000")]  # Different length

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        volume_series = Series[Qty](
            timestamps=tuple(timestamps[:1]),
            values=tuple(volume_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series, volume=volume_series)
        with pytest.raises(
            ValueError, match="Close and volume series must have the same length"
        ):
            obv(ctx)

    def test_obv_metadata_inheritance(self):
        """Test that OBV preserves input series metadata."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        close_values = [Decimal("100"), Decimal("101")]
        volume_values = [Decimal("1000"), Decimal("1500")]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="ETHUSDT",
            timeframe="4h",
        )

        volume_series = Series[Qty](
            timestamps=tuple(timestamps),
            values=tuple(volume_values),
            symbol="ETHUSDT",
            timeframe="4h",
        )

        ctx = SeriesContext(close=close_series, volume=volume_series)
        result = obv(ctx)

        assert result.symbol == "ETHUSDT"
        assert result.timeframe == "4h"

    def test_obv_single_value(self):
        """Test OBV with single value."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        close_values = [Decimal("100")]
        volume_values = [Decimal("1000")]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        volume_series = Series[Qty](
            timestamps=tuple(timestamps),
            values=tuple(volume_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(close=close_series, volume=volume_series)
        result = obv(ctx)

        assert len(result.timestamps) == 1
        assert len(result.values) == 1
        assert result.values[0] == volume_values[0]
