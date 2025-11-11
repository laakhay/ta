"""Tests for select primitive with derived price fields."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.primitives import select
from laakhay.ta.registry.models import SeriesContext


def _make_series(values: list[int | float | Decimal], symbol: str = "BTCUSDT", timeframe: str = "1h") -> Series[Price]:
    """Helper to create a Series from values."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = tuple(base + timedelta(hours=i) for i in range(len(values)))
    price_values = tuple(Decimal(str(v)) for v in values)
    return Series[Price](timestamps=timestamps, values=price_values, symbol=symbol, timeframe=timeframe)


class TestSelectDerivedFields:
    """Tests for derived price fields in select primitive."""

    def test_hlc3_calculation(self):
        """Test hlc3 (typical price) calculation: (high + low + close) / 3"""
        high = _make_series([110, 115, 120])
        low = _make_series([95, 100, 105])
        close = _make_series([105, 110, 115])
        ctx = SeriesContext(high=high, low=low, close=close)

        result = select(ctx, field="hlc3")

        assert result.symbol == high.symbol
        assert result.timeframe == high.timeframe
        assert len(result.values) == 3
        # First bar: (110 + 95 + 105) / 3 = 310 / 3 = 103.333...
        assert abs(result.values[0] - Decimal("103.3333333333333333333333333")) < Decimal("0.0001")
        # Second bar: (115 + 100 + 110) / 3 = 325 / 3 = 108.333...
        assert abs(result.values[1] - Decimal("108.3333333333333333333333333")) < Decimal("0.0001")
        # Third bar: (120 + 105 + 115) / 3 = 340 / 3 = 113.333...
        assert abs(result.values[2] - Decimal("113.3333333333333333333333333")) < Decimal("0.0001")

    def test_hlc3_case_insensitive(self):
        """Test that hlc3 is case-insensitive"""
        high = _make_series([110])
        low = _make_series([95])
        close = _make_series([105])
        ctx = SeriesContext(high=high, low=low, close=close)

        result_upper = select(ctx, field="HLC3")
        result_lower = select(ctx, field="hlc3")
        result_mixed = select(ctx, field="Hlc3")

        assert result_upper.values == result_lower.values
        assert result_lower.values == result_mixed.values

    def test_typical_price_alias(self):
        """Test that typical_price is an alias for hlc3"""
        high = _make_series([110, 115])
        low = _make_series([95, 100])
        close = _make_series([105, 110])
        ctx = SeriesContext(high=high, low=low, close=close)

        hlc3_result = select(ctx, field="hlc3")
        typical_price_result = select(ctx, field="typical_price")

        assert hlc3_result.values == typical_price_result.values

    def test_hlc3_missing_fields(self):
        """Test that hlc3 raises error when required fields are missing"""
        high = _make_series([110])
        low = _make_series([95])
        ctx = SeriesContext(high=high, low=low)

        with pytest.raises(ValueError, match="missing required fields.*close"):
            select(ctx, field="hlc3")

    def test_ohlc4_calculation(self):
        """Test ohlc4 (average price) calculation: (open + high + low + close) / 4"""
        open_series = _make_series([100, 105, 110])
        high = _make_series([110, 115, 120])
        low = _make_series([95, 100, 105])
        close = _make_series([105, 110, 115])
        ctx = SeriesContext(open=open_series, high=high, low=low, close=close)

        result = select(ctx, field="ohlc4")

        assert result.symbol == open_series.symbol
        assert result.timeframe == open_series.timeframe
        assert len(result.values) == 3
        # First bar: (100 + 110 + 95 + 105) / 4 = 410 / 4 = 102.5
        assert result.values[0] == Decimal("102.5")
        # Second bar: (105 + 115 + 100 + 110) / 4 = 430 / 4 = 107.5
        assert result.values[1] == Decimal("107.5")
        # Third bar: (110 + 120 + 105 + 115) / 4 = 450 / 4 = 112.5
        assert result.values[2] == Decimal("112.5")

    def test_weighted_close_alias(self):
        """Test that weighted_close is an alias for ohlc4"""
        open_series = _make_series([100])
        high = _make_series([110])
        low = _make_series([95])
        close = _make_series([105])
        ctx = SeriesContext(open=open_series, high=high, low=low, close=close)

        ohlc4_result = select(ctx, field="ohlc4")
        weighted_close_result = select(ctx, field="weighted_close")

        assert ohlc4_result.values == weighted_close_result.values

    def test_ohlc4_missing_fields(self):
        """Test that ohlc4 raises error when required fields are missing"""
        high = _make_series([110])
        low = _make_series([95])
        close = _make_series([105])
        ctx = SeriesContext(high=high, low=low, close=close)

        with pytest.raises(ValueError, match="missing required fields.*open"):
            select(ctx, field="ohlc4")

    def test_hl2_calculation(self):
        """Test hl2 (mid price) calculation: (high + low) / 2"""
        high = _make_series([110, 115, 120])
        low = _make_series([95, 100, 105])
        ctx = SeriesContext(high=high, low=low)

        result = select(ctx, field="hl2")

        assert result.symbol == high.symbol
        assert result.timeframe == high.timeframe
        assert len(result.values) == 3
        # First bar: (110 + 95) / 2 = 205 / 2 = 102.5
        assert result.values[0] == Decimal("102.5")
        # Second bar: (115 + 100) / 2 = 215 / 2 = 107.5
        assert result.values[1] == Decimal("107.5")
        # Third bar: (120 + 105) / 2 = 225 / 2 = 112.5
        assert result.values[2] == Decimal("112.5")

    def test_median_price_alias(self):
        """Test that median_price is an alias for hl2"""
        high = _make_series([110])
        low = _make_series([95])
        ctx = SeriesContext(high=high, low=low)

        hl2_result = select(ctx, field="hl2")
        median_price_result = select(ctx, field="median_price")

        assert hl2_result.values == median_price_result.values

    def test_hl2_missing_fields(self):
        """Test that hl2 raises error when required fields are missing"""
        high = _make_series([110])
        ctx = SeriesContext(high=high)

        with pytest.raises(ValueError, match="missing required fields.*low"):
            select(ctx, field="hl2")

    def test_range_calculation(self):
        """Test range calculation: high - low"""
        high = _make_series([110, 115, 120])
        low = _make_series([95, 100, 105])
        ctx = SeriesContext(high=high, low=low)

        result = select(ctx, field="range")

        assert result.symbol == high.symbol
        assert result.timeframe == high.timeframe
        assert len(result.values) == 3
        # First bar: 110 - 95 = 15
        assert result.values[0] == Decimal("15")
        # Second bar: 115 - 100 = 15
        assert result.values[1] == Decimal("15")
        # Third bar: 120 - 105 = 15
        assert result.values[2] == Decimal("15")

    def test_range_missing_fields(self):
        """Test that range raises error when required fields are missing"""
        high = _make_series([110])
        ctx = SeriesContext(high=high)

        with pytest.raises(ValueError, match="missing required fields.*low"):
            select(ctx, field="range")

    def test_upper_wick_calculation(self):
        """Test upper_wick calculation: high - max(open, close)"""
        high = _make_series([110, 115, 120])
        open_series = _make_series([100, 105, 110])
        close = _make_series([105, 110, 115])
        ctx = SeriesContext(high=high, open=open_series, close=close)

        result = select(ctx, field="upper_wick")

        assert result.symbol == high.symbol
        assert result.timeframe == high.timeframe
        assert len(result.values) == 3
        # First bar: 110 - max(100, 105) = 110 - 105 = 5
        assert result.values[0] == Decimal("5")
        # Second bar: 115 - max(105, 110) = 115 - 110 = 5
        assert result.values[1] == Decimal("5")
        # Third bar: 120 - max(110, 115) = 120 - 115 = 5
        assert result.values[2] == Decimal("5")

    def test_upper_wick_when_close_greater_than_open(self):
        """Test upper_wick when close > open"""
        high = _make_series([110])
        open_series = _make_series([100])
        close = _make_series([108])  # close > open
        ctx = SeriesContext(high=high, open=open_series, close=close)

        result = select(ctx, field="upper_wick")

        # 110 - max(100, 108) = 110 - 108 = 2
        assert result.values[0] == Decimal("2")

    def test_upper_wick_when_open_greater_than_close(self):
        """Test upper_wick when open > close"""
        high = _make_series([110])
        open_series = _make_series([108])
        close = _make_series([100])  # open > close
        ctx = SeriesContext(high=high, open=open_series, close=close)

        result = select(ctx, field="upper_wick")

        # 110 - max(108, 100) = 110 - 108 = 2
        assert result.values[0] == Decimal("2")

    def test_upper_wick_missing_fields(self):
        """Test that upper_wick raises error when required fields are missing"""
        high = _make_series([110])
        open_series = _make_series([100])
        ctx = SeriesContext(high=high, open=open_series)

        with pytest.raises(ValueError, match="missing required fields.*close"):
            select(ctx, field="upper_wick")

    def test_lower_wick_calculation(self):
        """Test lower_wick calculation: min(open, close) - low"""
        open_series = _make_series([100, 105, 110])
        close = _make_series([105, 110, 115])
        low = _make_series([95, 100, 105])
        ctx = SeriesContext(open=open_series, close=close, low=low)

        result = select(ctx, field="lower_wick")

        assert result.symbol == open_series.symbol
        assert result.timeframe == open_series.timeframe
        assert len(result.values) == 3
        # First bar: min(100, 105) - 95 = 100 - 95 = 5
        assert result.values[0] == Decimal("5")
        # Second bar: min(105, 110) - 100 = 105 - 100 = 5
        assert result.values[1] == Decimal("5")
        # Third bar: min(110, 115) - 105 = 110 - 105 = 5
        assert result.values[2] == Decimal("5")

    def test_lower_wick_when_close_greater_than_open(self):
        """Test lower_wick when close > open"""
        open_series = _make_series([100])
        close = _make_series([108])  # close > open
        low = _make_series([95])
        ctx = SeriesContext(open=open_series, close=close, low=low)

        result = select(ctx, field="lower_wick")

        # min(100, 108) - 95 = 100 - 95 = 5
        assert result.values[0] == Decimal("5")

    def test_lower_wick_when_open_greater_than_close(self):
        """Test lower_wick when open > close"""
        open_series = _make_series([108])
        close = _make_series([100])  # open > close
        low = _make_series([95])
        ctx = SeriesContext(open=open_series, close=close, low=low)

        result = select(ctx, field="lower_wick")

        # min(108, 100) - 95 = 100 - 95 = 5
        assert result.values[0] == Decimal("5")

    def test_lower_wick_missing_fields(self):
        """Test that lower_wick raises error when required fields are missing"""
        open_series = _make_series([100])
        close = _make_series([105])
        ctx = SeriesContext(open=open_series, close=close)

        with pytest.raises(ValueError, match="missing required fields.*low"):
            select(ctx, field="lower_wick")

    def test_backward_compatibility_standard_fields(self):
        """Test that standard fields (close, high, low, open, volume) still work"""
        close = _make_series([105, 110, 115])
        high = _make_series([110, 115, 120])
        low = _make_series([95, 100, 105])
        open_series = _make_series([100, 105, 110])
        volume = _make_series([1000, 1200, 1500])
        ctx = SeriesContext(close=close, high=high, low=low, open=open_series, volume=volume)

        # Test all standard fields
        assert select(ctx, field="close").values == close.values
        assert select(ctx, field="high").values == high.values
        assert select(ctx, field="low").values == low.values
        assert select(ctx, field="open").values == open_series.values
        assert select(ctx, field="volume").values == volume.values

    def test_unknown_field_raises_error(self):
        """Test that unknown field raises appropriate error"""
        close = _make_series([105])
        ctx = SeriesContext(close=close)

        with pytest.raises(ValueError, match="missing required field 'unknown_field'"):
            select(ctx, field="unknown_field")

    def test_derived_fields_with_single_bar(self):
        """Test derived fields work correctly with single bar"""
        high = _make_series([110])
        low = _make_series([95])
        close = _make_series([105])
        open_series = _make_series([100])
        ctx = SeriesContext(high=high, low=low, close=close, open=open_series)

        hlc3 = select(ctx, field="hlc3")
        ohlc4 = select(ctx, field="ohlc4")
        hl2 = select(ctx, field="hl2")
        range_val = select(ctx, field="range")
        upper_wick = select(ctx, field="upper_wick")
        lower_wick = select(ctx, field="lower_wick")

        assert len(hlc3.values) == 1
        assert len(ohlc4.values) == 1
        assert len(hl2.values) == 1
        assert len(range_val.values) == 1
        assert len(upper_wick.values) == 1
        assert len(lower_wick.values) == 1

    def test_derived_fields_with_empty_series(self):
        """Test that derived fields handle empty series correctly"""
        high = _make_series([])
        low = _make_series([])
        close = _make_series([])
        open_series = _make_series([])
        ctx = SeriesContext(high=high, low=low, close=close, open=open_series)

        hlc3 = select(ctx, field="hlc3")
        ohlc4 = select(ctx, field="ohlc4")
        hl2 = select(ctx, field="hl2")
        range_val = select(ctx, field="range")

        assert len(hlc3.values) == 0
        assert len(ohlc4.values) == 0
        assert len(hl2.values) == 0
        assert len(range_val.values) == 0

    def test_derived_fields_preserve_metadata(self):
        """Test that derived fields preserve symbol and timeframe metadata"""
        high = _make_series([110], symbol="ETHUSDT", timeframe="4h")
        low = _make_series([95], symbol="ETHUSDT", timeframe="4h")
        close = _make_series([105], symbol="ETHUSDT", timeframe="4h")
        ctx = SeriesContext(high=high, low=low, close=close)

        hlc3 = select(ctx, field="hlc3")

        assert hlc3.symbol == "ETHUSDT"
        assert hlc3.timeframe == "4h"

    def test_all_derived_fields_together(self):
        """Test all derived fields can be calculated from same context"""
        high = _make_series([110, 115])
        low = _make_series([95, 100])
        close = _make_series([105, 110])
        open_series = _make_series([100, 105])
        ctx = SeriesContext(high=high, low=low, close=close, open=open_series)

        # All should work without errors
        hlc3 = select(ctx, field="hlc3")
        ohlc4 = select(ctx, field="ohlc4")
        hl2 = select(ctx, field="hl2")
        range_val = select(ctx, field="range")
        upper_wick = select(ctx, field="upper_wick")
        lower_wick = select(ctx, field="lower_wick")

        assert len(hlc3.values) == 2
        assert len(ohlc4.values) == 2
        assert len(hl2.values) == 2
        assert len(range_val.values) == 2
        assert len(upper_wick.values) == 2
        assert len(lower_wick.values) == 2
