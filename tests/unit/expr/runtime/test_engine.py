"""Tests for evaluation engine."""

from datetime import UTC, datetime
from decimal import Decimal

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.expr.ir.nodes import BinaryOpNode, LiteralNode
from laakhay.ta.expr.runtime.engine import Engine


class TestEngine:
    """Test evaluation engine functionality."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = Engine()
        assert engine._cache == {}

    def test_literal_method(self):
        """Test engine.literal() convenience method."""
        engine = Engine()
        literal = engine.literal(42)

        assert isinstance(literal, LiteralNode)
        assert literal.value == 42

    def test_evaluate_literal_series(self):
        """Test evaluating a literal series."""
        engine = Engine()

        # Create test series
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal("100")]
        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        literal = LiteralNode(series)
        dataset = {}
        result = engine.evaluate(literal, dataset)

        assert result == series

    def test_evaluate_literal_scalar(self):
        """Test evaluating a literal scalar."""
        engine = Engine()

        literal = LiteralNode(42)
        dataset = {}
        result = engine.evaluate(literal, dataset)

        # Scalar literals should return a scalar series
        assert isinstance(result, Series)
        assert result.symbol == "__SCALAR__"
        assert result.timeframe == "1s"
        assert len(result.timestamps) == 1
        assert result.values[0] == 42

    def test_evaluate_binary_operation(self):
        """Test evaluating a binary operation."""
        engine = Engine()

        # Create test series
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal("100")]
        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        # Create binary operation: series + 10
        left = LiteralNode(series)
        right = LiteralNode(10)
        binary_op = BinaryOpNode("add", left, right)

        dataset = {}
        result = engine.evaluate(binary_op, dataset)

        # Should return series with values [110]
        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.values) == 1
        assert result.values[0] == Decimal("110")

    def test_evaluate_with_dataset(self):
        """Test evaluating expression with dataset context."""
        engine = Engine()

        # Create test series
        timestamps = [datetime(2024, 1, 1, tzinfo=UTC)]
        values = [Decimal("100")]
        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        # Create literal that references dataset
        literal = LiteralNode(series)
        dataset = {"close": series}

        result = engine.evaluate(literal, dataset)

        # Should return the series regardless of dataset content
        assert result == series

    def test_evaluate_complex_expression(self):
        """Test evaluating a more complex expression."""
        engine = Engine()

        # Create test series
        timestamps = [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
        ]
        values = [Decimal("100"), Decimal("110")]
        series = Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        # Create expression: (series * 2) + 10
        left_mult = BinaryOpNode("mul", LiteralNode(series), LiteralNode(2))
        final_add = BinaryOpNode("add", left_mult, LiteralNode(10))

        dataset = {}
        result = engine.evaluate(final_add, dataset)

        # Should return series with values [210, 230]
        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.values) == 2
        assert result.values[0] == Decimal("210")
        assert result.values[1] == Decimal("230")

    def test_evaluate_empty_dataset(self):
        """Test evaluating with empty dataset."""
        engine = Engine()

        literal = LiteralNode(42)
        dataset = {}
        result = engine.evaluate(literal, dataset)

        assert isinstance(result, Series)
        assert result.symbol == "__SCALAR__"
        assert result.values[0] == 42

    def test_cache_initialization(self):
        """Test that cache is properly initialized."""
        engine = Engine()
        assert hasattr(engine, "_cache")
        assert isinstance(engine._cache, dict)
        assert len(engine._cache) == 0
