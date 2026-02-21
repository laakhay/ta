"""Tests for channel event patterns."""

from datetime import UTC, datetime

UTC = UTC
from decimal import Decimal

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.indicators.events.channel import enter, exit, in_channel, out
from laakhay.ta.registry.models import SeriesContext


class TestInChannel:
    """Test in_channel pattern - detect when price is inside channel."""

    def test_in_channel_basic(self):
        """Test basic in_channel detection."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
        ]
        # Price: 45, 50, 55, 40
        # Upper: 60, 60, 60, 60
        # Lower: 40, 40, 40, 40
        price_values = [Decimal("45"), Decimal("50"), Decimal("55"), Decimal("40")]
        upper_values = [Decimal("60"), Decimal("60"), Decimal("60"), Decimal("60")]
        lower_values = [Decimal("40"), Decimal("40"), Decimal("40"), Decimal("40")]

        price_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(price_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        upper_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(upper_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        lower_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(lower_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=price_series)
        result = in_channel(ctx, price=price_series, upper=upper_series, lower=lower_series)

        assert len(result) == 4
        # First: True (45 >= 40 and 45 <= 60)
        assert result.values[0] is True
        # Second: True (50 >= 40 and 50 <= 60)
        assert result.values[1] is True
        # Third: True (55 >= 40 and 55 <= 60)
        assert result.values[2] is True
        # Fourth: True (40 >= 40 and 40 <= 60) - exactly on lower bound
        assert result.values[3] is True

    def test_in_channel_with_scalars(self):
        """Test in_channel with scalar bounds."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
        ]
        # Price: 45, 50, 55
        price_values = [Decimal("45"), Decimal("50"), Decimal("55")]

        price_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(price_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=price_series)
        # Channel: 40 to 60
        result = in_channel(ctx, price=price_series, upper=60, lower=40)

        assert len(result) == 3
        assert all(result.values)  # All should be True (all within 40-60)

    def test_in_channel_outside(self):
        """Test in_channel when price is outside."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        # Price: 30, 70 (outside 40-60 channel)
        price_values = [Decimal("30"), Decimal("70")]

        price_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(price_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=price_series)
        result = in_channel(ctx, price=price_series, upper=60, lower=40)

        assert len(result) == 2
        assert all(v is False for v in result.values)  # Both outside


class TestOut:
    """Test out pattern - detect when price is outside channel."""

    def test_out_basic(self):
        """Test basic out detection."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
        ]
        # Price: 30, 50, 70
        # Channel: 40-60
        price_values = [Decimal("30"), Decimal("50"), Decimal("70")]

        price_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(price_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=price_series)
        result = out(ctx, price=price_series, upper=60, lower=40)

        assert len(result) == 3
        # First: True (30 < 40)
        assert result.values[0] is True
        # Second: False (50 is inside)
        assert result.values[1] is False
        # Third: True (70 > 60)
        assert result.values[2] is True

    def test_out_alignment_uses_same_timestamps_for_bounds(self):
        """Regression: upper/lower must be aligned to the exact same timestamps as price."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
            datetime(2024, 1, 5, tzinfo=UTC),
        ]
        price_series = Series[Price](
            timestamps=tuple(timestamps),
            values=(Decimal("10"), Decimal("20"), Decimal("30"), Decimal("40"), Decimal("50")),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        upper_series = Series[Price](
            timestamps=tuple(timestamps),
            values=(Decimal("15"), Decimal("25"), Decimal("35"), Decimal("45"), Decimal("55")),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        # Lower starts one bar later to force re-alignment.
        lower_series = Series[Price](
            timestamps=tuple(timestamps[1:]),
            values=(Decimal("18"), Decimal("28"), Decimal("38"), Decimal("48")),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=price_series)
        result = out(ctx, price=price_series, upper=upper_series, lower=lower_series)

        assert len(result) == 4
        # At 2024-01-02: 20 is between 18 and 25, so not outside.
        assert result.values[0] is False


class TestEnter:
    """Test enter pattern - detect when price enters channel."""

    def test_enter_basic(self):
        """Test basic enter detection."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
        ]
        # Price: 30 (outside), 35 (outside), 45 (inside), 50 (inside)
        # Channel: 40-60
        price_values = [Decimal("30"), Decimal("35"), Decimal("45"), Decimal("50")]

        price_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(price_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=price_series)
        result = enter(ctx, price=price_series, upper=60, lower=40)

        assert len(result) == 4
        # First: False (no previous)
        assert result.values[0] is False
        # Second: False (35 still outside, 30 was outside)
        assert result.values[1] is False
        # Third: True (45 is inside AND 35 was outside) - ENTERED!
        assert result.values[2] is True
        # Fourth: False (50 is inside but 45 was already inside)
        assert result.values[3] is False


class TestExit:
    """Test exit pattern - detect when price exits channel."""

    def test_exit_basic(self):
        """Test basic exit detection."""
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
        ]
        # Price: 50 (inside), 55 (inside), 35 (outside), 30 (outside)
        # Channel: 40-60
        price_values = [Decimal("50"), Decimal("55"), Decimal("35"), Decimal("30")]

        price_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(price_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ctx = SeriesContext(price=price_series)
        result = exit(ctx, price=price_series, upper=60, lower=40)

        assert len(result) == 4
        # First: False (no previous)
        assert result.values[0] is False
        # Second: False (55 still inside, 50 was inside)
        assert result.values[1] is False
        # Third: True (35 is outside AND 55 was inside) - EXITED!
        assert result.values[2] is True
        # Fourth: False (30 is outside but 35 was already outside)
        assert result.values[3] is False
