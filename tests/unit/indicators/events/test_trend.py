"""Tests for trend event patterns."""

from datetime import UTC, datetime
from decimal import Decimal

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.events.trend import falling, falling_pct, rising, rising_pct
from laakhay.ta.registry.models import SeriesContext


class TestRising:
    """Test rising pattern - detect when series is moving up."""

    def test_rising_basic(self):
        """Test basic rising detection."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
        ]
        # Values: 10, 15, 12, 20
        values = [Decimal("10"), Decimal("15"), Decimal("12"), Decimal("20")]

        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=series)
        result = rising(ctx, a=series)

        assert len(result) == 4
        # First: False (no previous)
        assert result.values[0] is False
        # Second: True (15 > 10)
        assert result.values[1] is True
        # Third: False (12 < 15)
        assert result.values[2] is False
        # Fourth: True (20 > 12)
        assert result.values[3] is True

    def test_rising_empty_series(self):
        """Test rising with empty series."""
        empty_series = Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h")

        ctx = SeriesContext(price=empty_series)
        result = rising(ctx)

        assert len(result) == 0

    def test_rising_single_value(self):
        """Test rising with single value."""
        series = Series[Price](
            timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
            values=(Decimal("10"),),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=series)
        result = rising(ctx)

        assert len(result) == 1
        assert result.values[0] is False  # No previous to compare


class TestFalling:
    """Test falling pattern - detect when series is moving down."""

    def test_falling_basic(self):
        """Test basic falling detection."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
        ]
        # Values: 20, 15, 18, 10
        values = [Decimal("20"), Decimal("15"), Decimal("18"), Decimal("10")]

        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=series)
        result = falling(ctx, a=series)

        assert len(result) == 4
        # First: False (no previous)
        assert result.values[0] is False
        # Second: True (15 < 20)
        assert result.values[1] is True
        # Third: False (18 > 15)
        assert result.values[2] is False
        # Fourth: True (10 < 18)
        assert result.values[3] is True


class TestRisingPct:
    """Test rising_pct pattern - detect when series rises by percentage."""

    def test_rising_pct_basic(self):
        """Test basic rising_pct detection."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
        ]
        # Values: 100, 104, 106, 110
        # 5% threshold: 100 * 1.05 = 105
        values = [Decimal("100"), Decimal("104"), Decimal("106"), Decimal("110")]

        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=series)
        result = rising_pct(ctx, a=series, pct=5)

        assert len(result) == 4
        # First: False (no previous)
        assert result.values[0] is False
        # Second: False (104 < 105 threshold)
        assert result.values[1] is False
        # Third: False (106 < 105.2 threshold from 104)
        assert result.values[2] is False
        # Fourth: True (110 >= 111.3 threshold from 106? Wait, let me recalculate)
        # Actually: 110 >= 106 * 1.05 = 111.3? No, 110 < 111.3
        # Let me fix: 110 >= 106 * 1.05 = 111.3? Actually 106 * 1.05 = 111.3, so 110 < 111.3
        # So it should be False. Let me adjust the test.
        assert result.values[3] is False

    def test_rising_pct_threshold_met(self):
        """Test rising_pct when threshold is met."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        # Values: 100, 110 (10% rise)
        values = [Decimal("100"), Decimal("110")]

        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=series)
        result = rising_pct(ctx, a=series, pct=5)  # 5% threshold

        assert len(result) == 2
        # First: False (no previous)
        assert result.values[0] is False
        # Second: True (110 >= 100 * 1.05 = 105)
        assert result.values[1] is True

    def test_rising_pct_exact_threshold(self):
        """Test rising_pct with exact threshold."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        # Values: 100, 105 (exactly 5% rise)
        values = [Decimal("100"), Decimal("105")]

        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=series)
        result = rising_pct(ctx, a=series, pct=5)

        assert len(result) == 2
        assert result.values[0] is False
        # Second: True (105 >= 105 threshold)
        assert result.values[1] is True


class TestFallingPct:
    """Test falling_pct pattern - detect when series falls by percentage."""

    def test_falling_pct_basic(self):
        """Test basic falling_pct detection."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        # Values: 100, 90 (10% fall)
        values = [Decimal("100"), Decimal("90")]

        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=series)
        result = falling_pct(ctx, a=series, pct=5)  # 5% threshold

        assert len(result) == 2
        # First: False (no previous)
        assert result.values[0] is False
        # Second: True (90 <= 100 * 0.95 = 95)
        assert result.values[1] is True

    def test_falling_pct_exact_threshold(self):
        """Test falling_pct with exact threshold."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        # Values: 100, 95 (exactly 5% fall)
        values = [Decimal("100"), Decimal("95")]

        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=series)
        result = falling_pct(ctx, a=series, pct=5)

        assert len(result) == 2
        assert result.values[0] is False
        # Second: True (95 <= 95 threshold)
        assert result.values[1] is True

    def test_falling_pct_threshold_not_met(self):
        """Test falling_pct when threshold is not met."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        # Values: 100, 98 (only 2% fall, need 5%)
        values = [Decimal("100"), Decimal("98")]

        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=series)
        result = falling_pct(ctx, a=series, pct=5)

        assert len(result) == 2
        assert result.values[0] is False
        # Second: False (98 > 95 threshold)
        assert result.values[1] is False
