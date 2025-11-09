"""Tests for crossing event patterns."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.events.crossing import cross, crossdown, crossup
from laakhay.ta.registry.models import SeriesContext


class TestCrossUp:
    """Test crossup pattern - detect when series a crosses above series b."""

    def test_crossup_basic(self):
        """Test basic crossup detection."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
        ]
        # a starts below b, then crosses above
        a_values = [Decimal("10"), Decimal("15"), Decimal("25"), Decimal("30")]
        b_values = [Decimal("20"), Decimal("20"), Decimal("20"), Decimal("20")]
        
        a_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(a_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        b_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(b_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        ctx = SeriesContext(price=a_series)
        result = crossup(ctx, a=a_series, b=b_series)
        
        assert len(result) == 4
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        
        # First value: False (no previous)
        assert result.values[0] is False
        
        # Second value: False (a=15 < b=20, still below)
        assert result.values[1] is False
        
        # Third value: True (a=25 > b=20 AND previous a=15 <= b=20) - CROSS!
        assert result.values[2] is True
        
        # Fourth value: False (a=30 > b=20 but previous a=25 > b=20, already crossed)
        assert result.values[3] is False

    def test_crossup_with_scalar(self):
        """Test crossup with scalar threshold."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
        ]
        # Price crosses above 50
        price_values = [Decimal("40"), Decimal("45"), Decimal("55")]
        
        price_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(price_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        ctx = SeriesContext(price=price_series)
        result = crossup(ctx, a=price_series, b=50)
        
        assert len(result) == 3
        # First: False (no previous)
        assert result.values[0] is False
        # Second: False (45 < 50)
        assert result.values[1] is False
        # Third: True (55 > 50 AND 45 <= 50) - CROSS!
        assert result.values[2] is True

    def test_crossup_no_cross(self):
        """Test crossup when no crossing occurs."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
        ]
        # a stays below b
        a_values = [Decimal("10"), Decimal("15"), Decimal("18")]
        b_values = [Decimal("20"), Decimal("20"), Decimal("20")]
        
        a_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(a_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        b_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(b_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        ctx = SeriesContext(price=a_series)
        result = crossup(ctx, a=a_series, b=b_series)
        
        assert all(v is False for v in result.values)

    def test_crossup_empty_series(self):
        """Test crossup with empty series."""
        empty_series = Series[Price](
            timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h"
        )
        
        ctx = SeriesContext(price=empty_series)
        result = crossup(ctx)
        
        assert len(result) == 0
        assert result.symbol == "BTCUSDT"

    def test_crossup_single_value(self):
        """Test crossup with single value (should return False)."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        a_series = Series[Price](
            timestamps=tuple(timestamps),
            values=(Decimal("10"),),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        b_series = Series[Price](
            timestamps=tuple(timestamps),
            values=(Decimal("20"),),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        ctx = SeriesContext(price=a_series)
        result = crossup(ctx, a=a_series, b=b_series)
        
        assert len(result) == 1
        assert result.values[0] is False  # No previous to compare


class TestCrossDown:
    """Test crossdown pattern - detect when series a crosses below series b."""

    def test_crossdown_basic(self):
        """Test basic crossdown detection."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
        ]
        # a starts above b, then crosses below
        a_values = [Decimal("30"), Decimal("25"), Decimal("15"), Decimal("10")]
        b_values = [Decimal("20"), Decimal("20"), Decimal("20"), Decimal("20")]
        
        a_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(a_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        b_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(b_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        ctx = SeriesContext(price=a_series)
        result = crossdown(ctx, a=a_series, b=b_series)
        
        assert len(result) == 4
        # First: False (no previous)
        assert result.values[0] is False
        # Second: False (a=25 > b=20, still above)
        assert result.values[1] is False
        # Third: True (a=15 < b=20 AND previous a=25 >= b=20) - CROSS!
        assert result.values[2] is True
        # Fourth: False (a=10 < b=20 but previous a=15 < b=20, already crossed)
        assert result.values[3] is False

    def test_crossdown_with_scalar(self):
        """Test crossdown with scalar threshold."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
        ]
        # Price crosses below 50
        price_values = [Decimal("60"), Decimal("55"), Decimal("45")]
        
        price_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(price_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        ctx = SeriesContext(price=price_series)
        result = crossdown(ctx, a=price_series, b=50)
        
        assert len(result) == 3
        # First: False (no previous)
        assert result.values[0] is False
        # Second: False (55 > 50)
        assert result.values[1] is False
        # Third: True (45 < 50 AND 55 >= 50) - CROSS!
        assert result.values[2] is True


class TestCross:
    """Test cross pattern - detect any crossing."""

    def test_cross_basic(self):
        """Test basic cross detection (either direction)."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
        ]
        # a crosses above, then crosses below
        a_values = [Decimal("10"), Decimal("15"), Decimal("25"), Decimal("15")]
        b_values = [Decimal("20"), Decimal("20"), Decimal("20"), Decimal("20")]
        
        a_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(a_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        b_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(b_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        ctx = SeriesContext(price=a_series)
        result = cross(ctx, a=a_series, b=b_series)
        
        assert len(result) == 4
        # First: False (no previous)
        assert result.values[0] is False
        # Second: False (no cross)
        assert result.values[1] is False
        # Third: True (crossup occurred)
        assert result.values[2] is True
        # Fourth: True (crossdown occurred: 15 < 20 AND previous 25 >= 20)
        assert result.values[3] is True

    def test_cross_no_cross(self):
        """Test cross when no crossing occurs."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        # a stays above b
        a_values = [Decimal("30"), Decimal("35")]
        b_values = [Decimal("20"), Decimal("20")]
        
        a_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(a_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        b_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(b_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        ctx = SeriesContext(price=a_series)
        result = cross(ctx, a=a_series, b=b_series)
        
        assert all(v is False for v in result.values)

