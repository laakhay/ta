"""Tests for VWAP indicator."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.registry.models import SeriesContext
from laakhay.ta.indicators.volume.vwap import vwap


class TestVWAPIndicator:
    """Test Volume Weighted Average Price indicator."""

    def test_vwap_basic_calculation(self):
        """Test basic VWAP calculation with valid data."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 1, 2, tzinfo=timezone.utc),
            datetime(2024, 1, 3, tzinfo=timezone.utc),
        ]
        high_values = [Decimal('101'), Decimal('102'), Decimal('103')]
        low_values = [Decimal('99'), Decimal('100'), Decimal('101')]
        close_values = [Decimal('100'), Decimal('101'), Decimal('102')]
        volume_values = [Decimal('1000'), Decimal('1500'), Decimal('800')]
        
        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(high_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(low_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        volume_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(volume_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(high=high_series, low=low_series, close=close_series, volume=volume_series)
        result = vwap(ctx)
        
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 3
        assert len(result.values) == 3
        
        # First value: typical price = (101 + 99 + 100) / 3 = 100
        # VWAP = 100 (first value)
        assert result.values[0] == Decimal('100')
        
        # Second value: typical price = (102 + 100 + 101) / 3 = 101
        # Cumulative volume = 1000 + 1500 = 2500
        # Cumulative volume*price = 100*1000 + 101*1500 = 100000 + 151500 = 251500
        # VWAP = 251500 / 2500 = 100.6
        expected_second = (Decimal('100') * Decimal('1000') + Decimal('101') * Decimal('1500')) / (Decimal('1000') + Decimal('1500'))
        assert abs(float(result.values[1]) - float(expected_second)) < 0.01

    def test_vwap_empty_series(self):
        """Test VWAP with empty input series."""
        empty_series = Series[Price](
            timestamps=(),
            values=(),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(high=empty_series, low=empty_series, close=empty_series, volume=empty_series)
        result = vwap(ctx)
        
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.timestamps) == 0
        assert len(result.values) == 0

    def test_vwap_missing_series(self):
        """Test VWAP with missing required series."""
        timestamps = [datetime(2024, 1, 1, tzinfo=timezone.utc)]
        values = [Decimal('100')]
        
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        # Test missing high
        ctx = SeriesContext(low=close_series, close=close_series, volume=close_series)
        with pytest.raises(ValueError, match="VWAP requires series: .* missing: .*high.*"):
            vwap(ctx)
        
        # Test missing low
        ctx = SeriesContext(high=close_series, close=close_series, volume=close_series)
        with pytest.raises(ValueError, match="VWAP requires series: .* missing: .*low.*"):
            vwap(ctx)
        
        # Test missing close
        ctx = SeriesContext(high=close_series, low=close_series, volume=close_series)
        with pytest.raises(ValueError, match="VWAP requires series: .* missing: .*close.*"):
            vwap(ctx)
        
        # Test missing volume
        ctx = SeriesContext(high=close_series, low=close_series, close=close_series)
        with pytest.raises(ValueError, match="VWAP requires series: .* missing: .*volume.*"):
            vwap(ctx)

    def test_vwap_different_lengths(self):
        """Test VWAP with different length series."""
        timestamps = [datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 2, tzinfo=timezone.utc)]
        values = [Decimal('100'), Decimal('101')]
        short_values = [Decimal('100')]  # Different length
        
        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        volume_series = Series[Price](
            timestamps=tuple(timestamps[:1]),
            values=tuple(short_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(high=high_series, low=low_series, close=close_series, volume=volume_series)
        with pytest.raises(ValueError, match="All series must have the same length"):
            vwap(ctx)

    def test_vwap_metadata_inheritance(self):
        """Test that VWAP preserves input series metadata."""
        timestamps = [datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 2, tzinfo=timezone.utc)]
        values = [Decimal('100'), Decimal('101')]
        
        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h"
        )
        
        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h"
        )
        
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h"
        )
        
        volume_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="ETHUSDT",
            timeframe="4h"
        )
        
        ctx = SeriesContext(high=high_series, low=low_series, close=close_series, volume=volume_series)
        result = vwap(ctx)
        
        assert result.symbol == "ETHUSDT"
        assert result.timeframe == "4h"

    def test_vwap_single_value(self):
        """Test VWAP with single value."""
        timestamps = [datetime(2024, 1, 1, tzinfo=timezone.utc)]
        values = [Decimal('100')]
        
        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        volume_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(high=high_series, low=low_series, close=close_series, volume=volume_series)
        result = vwap(ctx)
        
        assert len(result.timestamps) == 1
        assert len(result.values) == 1
        # Single value VWAP should equal typical price
        assert result.values[0] == Decimal('100')

    def test_vwap_zero_volume_fallback(self):
        """Test VWAP with zero volume (should fallback to typical price)."""
        timestamps = [datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 2, tzinfo=timezone.utc)]
        high_values = [Decimal('101'), Decimal('102')]
        low_values = [Decimal('99'), Decimal('100')]
        close_values = [Decimal('100'), Decimal('101')]
        volume_values = [Decimal('0'), Decimal('0')]  # Zero volume
        
        high_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(high_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        low_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(low_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        volume_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(volume_values),
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(high=high_series, low=low_series, close=close_series, volume=volume_series)
        result = vwap(ctx)
        
        # Should fallback to typical price when volume is zero
        expected_first = (Decimal('101') + Decimal('99') + Decimal('100')) / Decimal('3')
        expected_second = (Decimal('102') + Decimal('100') + Decimal('101')) / Decimal('3')
        
        assert abs(float(result.values[0]) - float(expected_first)) < 0.01
        assert abs(float(result.values[1]) - float(expected_second)) < 0.01
