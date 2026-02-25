"""Functional tests for indicator execution with Engine."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta import Bar, Engine, dataset, indicator
from laakhay.ta.core import OHLCV, Series
from laakhay.ta.core.types import Price


class TestIndicatorsFunctional:
    """Test indicators with real data and Engine evaluation."""

    def test_sma_indicator_execution(self):
        """Test SMA indicator execution with real data."""
        # Create sample bars
        bars = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 2, tzinfo=UTC),
                open=Price("102"),
                high=Price("108"),
                low=Price("98"),
                close=Price("106"),
                volume=Price("1200"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 3, tzinfo=UTC),
                open=Price("106"),
                high=Price("112"),
                low=Price("104"),
                close=Price("110"),
                volume=Price("1300"),
                is_closed=True,
            ),
        ]

        # Convert bars to OHLCV
        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")

        # Create dataset from OHLCV
        ds = dataset(ohlcv)

        # Create SMA indicator handle
        sma_2 = indicator("sma", period=2)

        # Test that we can get the schema
        schema = sma_2.schema
        assert schema["name"] == "sma"
        # Check that period parameter exists
        assert "period" in schema["params"]

        # Test indicator execution
        result = sma_2(ds)

        # Verify result
        assert isinstance(result, Series)
        assert len(result.values) == 3  # Full length 3
        # First SMA is at index 1: (102 + 106) / 2 = 104
        assert result.availability_mask[0] is False
        assert result.values[1] == Price(Decimal("104"))
        # Second SMA: (106 + 110) / 2 = 108
        assert result.values[2] == Price(Decimal("108"))

    def test_indicator_with_engine(self):
        """Test indicator execution through Engine."""
        # Create sample bars
        bars = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 2, tzinfo=UTC),
                open=Price("102"),
                high=Price("108"),
                low=Price("98"),
                close=Price("106"),
                volume=Price("1200"),
                is_closed=True,
            ),
        ]

        # Convert bars to OHLCV
        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")

        # Create dataset from OHLCV
        ds = dataset(ohlcv)

        # Create SMA indicator handle
        sma_2 = indicator("sma", period=2)

        # Test that indicator handle can be used as expression
        from laakhay.ta.expr.algebra.operators import _to_node
        from laakhay.ta.expr.ir.nodes import BinaryOpNode, LiteralNode

        # Create expression: sma + 10
        add_expr = BinaryOpNode("add", _to_node(sma_2), LiteralNode(10))

        # Evaluate with engine
        engine = Engine()
        result = engine.evaluate(add_expr, ds)

        # Verify result
        assert isinstance(result, Series)
        assert len(result.values) == 2  # SMA(2) on 2 bars = full length 2
        # SMA: (102 + 106) / 2 = 104, + 10 = 114 at index 1
        assert result.values[1] == Price(Decimal("114"))

    def test_multiple_indicators(self):
        """Test multiple indicators on same dataset."""
        # Create sample bars
        bars = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 2, tzinfo=UTC),
                open=Price("102"),
                high=Price("108"),
                low=Price("98"),
                close=Price("106"),
                volume=Price("1200"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 3, tzinfo=UTC),
                open=Price("106"),
                high=Price("112"),
                low=Price("104"),
                close=Price("110"),
                volume=Price("1300"),
                is_closed=True,
            ),
        ]

        # Convert bars to OHLCV
        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")

        # Create dataset from OHLCV
        ds = dataset(ohlcv)

        # Create multiple indicators
        sma_2 = indicator("sma", period=2)
        sma_3 = indicator("sma", period=3)

        # Test both indicators
        result_2 = sma_2(ds)
        result_3 = sma_3(ds)

        # Verify results
        assert isinstance(result_2, Series)
        assert isinstance(result_3, Series)
        assert len(result_2.values) == 3  # Full length 3
        assert len(result_3.values) == 3  # Full length 3

        # SMA(2) first result at index 1: (102 + 106) / 2 = 104
        assert result_2.values[1] == Price(Decimal("104"))
        # SMA(3) result at index 2: (102 + 106 + 110) / 3 = 106
        assert result_3.values[2] == Price(Decimal("106"))

    def test_indicator_error_handling(self):
        """Test indicator error handling."""
        # Create empty dataset
        ds = dataset()

        # Create SMA indicator
        sma_2 = indicator("sma", period=2)

        # Test that indicator raises appropriate error for empty dataset
        with pytest.raises(ValueError, match="SeriesContext has no series to operate on"):
            sma_2(ds)
