"""Tests for the new public API."""

from datetime import UTC, datetime

UTC = UTC
from decimal import Decimal

import pytest

# Import from main module to ensure indicators are registered
from laakhay.ta import Expression, IndicatorHandle, TASeries, ta
from laakhay.ta.core import Dataset, Series
from laakhay.ta.core.types import Price, Volume


class TestIndicatorHandle:
    """Test IndicatorHandle functionality."""

    def test_indicator_handle_creation(self):
        """Test creating indicator handles."""
        sma_handle = ta.indicator("sma", period=20)
        assert isinstance(sma_handle, IndicatorHandle)
        assert sma_handle.name == "sma"
        assert sma_handle.params == {"period": 20}

    def test_indicator_handle_schema(self):
        """Test indicator handle schema introspection."""
        sma_handle = ta.indicator("sma", period=20)
        schema = sma_handle.schema
        assert schema["name"] == "sma"
        assert schema["params"] == {"period": 20}
        assert "description" in schema

    def test_indicator_handle_describe(self):
        """Test indicator handle description."""
        sma_handle = ta.indicator("sma", period=20)
        description = sma_handle.describe()
        assert "sma" in description
        assert "period=20" in description

    def test_indicator_handle_call_with_series(self):
        """Test calling indicator handle with a series."""
        # Create test data
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
            datetime(2024, 1, 5, tzinfo=UTC),
        ]
        values = [
            Price(Decimal("100")),
            Price(Decimal("110")),
            Price(Decimal("120")),
            Price(Decimal("130")),
            Price(Decimal("140")),
        ]
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        sma_handle = ta.indicator("sma", period=3)
        result = sma_handle(close_series)

        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result) == 3  # SMA with period=3 on 5 data points

    def test_indicator_handle_call_with_dataset(self):
        """Test calling indicator handle with a dataset."""
        # Create test data
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
        ]
        values = [Price(Decimal("100")), Price(Decimal("110")), Price(Decimal("120"))]
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        dataset = Dataset()
        dataset.add("BTCUSDT", "1h", "close", close_series)

        sma_handle = ta.indicator("sma", period=2)
        result = sma_handle(dataset)

        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"

    def test_indicator_handle_invalid_name(self):
        """Test creating indicator handle with invalid name."""
        with pytest.raises(ValueError, match="Indicator 'invalid' not found"):
            ta.indicator("invalid", period=20)


class TestIndicatorHandleAlgebraicComposition:
    """Test algebraic composition of indicator handles."""

    def test_indicator_handle_addition(self):
        """Test adding indicator handles."""
        sma_fast = ta.indicator("sma", period=20)
        sma_slow = ta.indicator("sma", period=50)

        spread = sma_fast + sma_slow
        assert isinstance(spread, Expression)

    def test_indicator_handle_subtraction(self):
        """Test subtracting indicator handles."""
        sma_fast = ta.indicator("sma", period=20)
        sma_slow = ta.indicator("sma", period=50)

        spread = sma_fast - sma_slow
        assert isinstance(spread, Expression)

    def test_indicator_handle_multiplication(self):
        """Test multiplying indicator handles."""
        sma_handle = ta.indicator("sma", period=20)
        multiplier = 2

        result = sma_handle * multiplier
        assert isinstance(result, Expression)

    def test_indicator_handle_division(self):
        """Test dividing indicator handles."""
        sma_handle = ta.indicator("sma", period=20)
        divisor = 2

        result = sma_handle / divisor
        assert isinstance(result, Expression)

    def test_indicator_handle_comparison(self):
        """Test comparing indicator handles."""
        sma_fast = ta.indicator("sma", period=20)
        sma_slow = ta.indicator("sma", period=50)

        comparison = sma_fast > sma_slow
        assert isinstance(comparison, Expression)

    def test_indicator_handle_logical_operations(self):
        """Test logical operations on indicator handles."""
        sma_handle = ta.indicator("sma", period=20)
        threshold = 100

        logical = (sma_handle > threshold) & (sma_handle < 200)
        assert isinstance(logical, Expression)

    def test_indicator_handle_with_literal(self):
        """Test indicator handle with literal values."""
        sma_handle = ta.indicator("sma", period=20)
        bias = ta.literal(15)

        result = sma_handle + bias
        assert isinstance(result, Expression)


class TestTASeries:
    """Test TASeries functionality."""

    def test_ta_series_creation(self):
        """Test creating TASeries."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Price(Decimal("100"))]
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ta_series = ta(close_series)
        assert isinstance(ta_series, TASeries)

    def test_ta_series_with_additional_series(self):
        """Test TASeries with additional series."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        close_values = [Price(Decimal("100"))]
        volume_values = [Volume(Decimal("1000"))]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        volume_series = Series[Volume](
            timestamps=tuple(timestamps),
            values=tuple(volume_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ta_series = ta(close_series, volume=volume_series)
        assert isinstance(ta_series, TASeries)

    def test_ta_series_indicator_access(self):
        """Test accessing indicators on TASeries."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Price(Decimal("100"))]
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ta_series = ta(close_series)

        # Test that we can access indicator methods
        sma_func = ta_series.sma
        assert callable(sma_func)

        result = sma_func(period=20)
        assert isinstance(result, Expression)  # Should return Expression for algebraic composition

    def test_ta_series_invalid_indicator(self):
        """Test accessing invalid indicator on TASeries."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Price(Decimal("100"))]
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ta_series = ta(close_series)

        with pytest.raises(AttributeError, match="Indicator 'invalid' not found"):
            _ = ta_series.invalid

    def test_ta_series_algebraic_operations(self):
        """Test algebraic operations on TASeries."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Price(Decimal("100"))]
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        ta_series = ta(close_series)

        # Test addition
        result = ta_series + 10
        assert isinstance(result, Expression)

        # Test comparison
        result = ta_series > 50
        assert isinstance(result, Expression)


class TestLiteralFunction:
    """Test the literal function."""

    def test_literal_creation(self):
        """Test creating literal expressions."""
        literal_expr = ta.literal(15)
        assert isinstance(literal_expr, Expression)

    def test_literal_with_different_types(self):
        """Test creating literals with different types."""
        int_literal = ta.literal(15)
        float_literal = ta.literal(15.5)
        decimal_literal = ta.literal(Decimal("15.5"))

        assert isinstance(int_literal, Expression)
        assert isinstance(float_literal, Expression)
        assert isinstance(decimal_literal, Expression)


class TestPublicAPIIntegration:
    """Test integration of the public API with existing systems."""

    def test_vision_api_example(self):
        """Test the exact API example from the vision document."""
        # Create test data
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
            datetime(2024, 1, 4, tzinfo=UTC),
            datetime(2024, 1, 5, tzinfo=UTC),
        ]
        values = [
            Price(Decimal("100")),
            Price(Decimal("110")),
            Price(Decimal("120")),
            Price(Decimal("130")),
            Price(Decimal("140")),
        ]
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        # Vision API example
        sma_fast = ta.indicator("sma", period=20)
        sma_slow = ta.indicator("sma", period=50)
        rsi = ta.indicator("rsi", period=14)

        # Test algebraic composition
        spread = sma_fast - sma_slow
        bias = ta.literal(15)
        combo = (spread + bias) * rsi
        signal = (combo > 100) & (rsi < 30)

        # All should be expressions
        assert isinstance(spread, Expression)
        assert isinstance(combo, Expression)
        assert isinstance(signal, Expression)

        # Test calling with series
        result = sma_fast(close_series)
        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"

    def test_alternative_api_example(self):
        """Test the alternative API: ta(series).indicator()"""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Price(Decimal("100"))]
        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        # Alternative API
        sma_20 = ta(close_series).sma(20)
        rsi_14 = ta(close_series).rsi(14)

        assert isinstance(sma_20, Expression)  # Should return Expression for algebraic composition
        assert isinstance(rsi_14, Expression)  # Should return Expression for algebraic composition

        # Test algebraic composition
        strategy = (ta(close_series).sma(20) > ta(close_series).ema(12)) & (ta(close_series).rsi(14) < 30)
        assert isinstance(strategy, Expression)

    def test_multi_series_indicators(self):
        """Test multi-series indicators with the public API."""
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        close_values = [Price(Decimal("100"))]
        volume_values = [Volume(Decimal("1000"))]

        close_series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(close_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        volume_series = Series[Volume](
            timestamps=tuple(timestamps),
            values=tuple(volume_values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        # Test with TASeries
        obv_result = ta(close_series, volume=volume_series).obv()
        assert isinstance(obv_result, Expression)  # Should return Expression for algebraic composition

        # Test with indicator handles
        obv_handle = ta.indicator("obv")
        # This would need a dataset with both close and volume
        dataset = Dataset()
        dataset.add("BTCUSDT", "1h", "close", close_series)
        dataset.add("BTCUSDT", "1h", "volume", volume_series)

        obv_result2 = obv_handle(dataset)
        assert isinstance(obv_result2, Series)
