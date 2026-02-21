"""Functional tests for the Engine evaluation system."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta import Bar, Engine, dataset
from laakhay.ta.core import Series
from laakhay.ta.core.types import Price
from laakhay.ta.expr.algebra import BinaryOp, Literal, OperatorType


class TestEngineFunctional:
    """Test Engine with real data and expressions."""

    def test_engine_literal_evaluation(self):
        """Test Engine can evaluate literal expressions."""
        engine = Engine()

        # Create a literal expression
        literal_expr = Literal(42)

        # Create empty dataset
        empty_dataset = dataset()

        # Evaluate literal
        result = engine.evaluate(literal_expr, empty_dataset)

        assert isinstance(result, Series)
        assert len(result.values) == 1
        assert result.values[0] == Price(Decimal("42"))

    def test_engine_binary_operation(self):
        """Test Engine can evaluate binary operations."""
        engine = Engine()

        # Create binary expression: 10 + 20
        left = Literal(10)
        right = Literal(20)
        add_expr = BinaryOp(OperatorType.ADD, left, right)

        # Create empty dataset
        empty_dataset = dataset()

        # Evaluate expression
        result = engine.evaluate(add_expr, empty_dataset)

        assert isinstance(result, Series)
        assert len(result.values) == 1
        assert result.values[0] == Price(Decimal("30"))

    def test_engine_with_real_data(self):
        """Test Engine with real OHLCV data."""
        from laakhay.ta.core.ohlcv import OHLCV

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

        # Get close series using the improved dataset API
        close_series = ds["close"]

        # Create expression: close + 10
        literal_10 = Literal(10)
        add_expr = BinaryOp(OperatorType.ADD, Literal(close_series), literal_10)

        # Evaluate with engine
        engine = Engine()
        result = engine.evaluate(add_expr, ds)

        assert isinstance(result, Series)
        assert len(result.values) == 2
        # First close (102) + 10 = 112
        assert result.values[0] == Price(Decimal("112"))
        # Second close (106) + 10 = 116
        assert result.values[1] == Price(Decimal("116"))

    def test_engine_complex_expression(self):
        """Test Engine with complex nested expressions."""
        engine = Engine()

        # Create expression: (10 + 20) * 2
        inner_add = BinaryOp(OperatorType.ADD, Literal(10), Literal(20))
        multiply = BinaryOp(OperatorType.MUL, inner_add, Literal(2))

        empty_dataset = dataset()
        result = engine.evaluate(multiply, empty_dataset)

        assert isinstance(result, Series)
        assert len(result.values) == 1
        # (10 + 20) * 2 = 60
        assert result.values[0] == Price(Decimal("60"))

    def test_engine_error_handling(self):
        """Test Engine handles errors gracefully."""
        engine = Engine()

        # Create invalid expression: 10 / 0
        div_expr = BinaryOp(OperatorType.DIV, Literal(10), Literal(0))

        empty_dataset = dataset()

        # Should raise appropriate error
        with pytest.raises((ValueError, ZeroDivisionError)):
            engine.evaluate(div_expr, empty_dataset)
