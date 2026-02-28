"""Tests for canonical Evaluator."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.core.bar import Bar
from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.expr.algebra.operators import Expression
from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.execution.time_shift import parse_shift_periods
from laakhay.ta.expr.ir.nodes import (
    AggregateNode,
    FilterNode,
    LiteralNode,
    SourceRefNode,
    TimeShiftNode,
)
from laakhay.ta.expr.planner.evaluator import Evaluator


def create_test_dataset() -> Dataset:
    """Create a test dataset with OHLCV data."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    bars = [
        Bar.from_raw(base + timedelta(hours=i), 100 + i, 101 + i, 99 + i, 100 + i, 1000 + i, True) for i in range(10)
    ]
    ds = Dataset()
    ds.add_series("BTCUSDT", "1h", OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h"))
    return ds


def _extract_single_series(result, symbol: str = "BTCUSDT", timeframe: str = "1h") -> Series:
    if isinstance(result, Series):
        return result
    return result[(symbol, timeframe, "default")]


class TestEvaluator:
    """Test Evaluator functionality."""

    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        evaluator = Evaluator()
        assert evaluator._cache == {}
        assert len(evaluator._cache) == 0

    def test_evaluate_simple_expression(self):
        """Test evaluating a simple expression."""
        evaluator = Evaluator()
        ds = create_test_dataset()

        expr = compile_expression("BTC.price > 100")
        result = _extract_single_series(evaluator.evaluate(expr, ds))

        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.values) > 0

    def test_evaluate_with_indicator(self):
        """Test evaluating expression with indicator."""
        evaluator = Evaluator()
        ds = create_test_dataset()

        expr = compile_expression("sma(BTC.price, period=5)")
        result = _extract_single_series(evaluator.evaluate(expr, ds))

        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"
        assert len(result.values) > 0

    def test_evaluate_multi_symbol_timeframe(self):
        """Test evaluating for multiple symbol/timeframe combinations."""
        evaluator = Evaluator()
        ds = create_test_dataset()

        # Add another symbol
        base = datetime(2024, 1, 1, tzinfo=UTC)
        eth_bars = [
            Bar.from_raw(base + timedelta(hours=i), 200 + i, 201 + i, 199 + i, 200 + i, 2000 + i, True)
            for i in range(10)
        ]
        ds.add_series("ETHUSDT", "1h", OHLCV.from_bars(eth_bars, symbol="ETHUSDT", timeframe="1h"))

        expr = compile_expression("BTC.price > 100")
        results = evaluator.evaluate(expr, ds)

        assert isinstance(results, dict)
        assert ("BTCUSDT", "1h", "default") in results
        assert ("ETHUSDT", "1h", "default") in results

    def test_evaluate_source_expression(self):
        """Test evaluating SourceExpression."""
        evaluator = Evaluator()
        ds = create_test_dataset()

        # Create SourceRefNode directly
        source_expr = SourceRefNode(
            symbol="BTCUSDT",
            field="price",
            exchange=None,
            timeframe="1h",
            source="ohlcv",
        )

        result = _extract_single_series(evaluator.evaluate(Expression(source_expr), ds))

        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"
        assert len(result.values) == 10

    def test_evaluate_filter_expression(self):
        """Test evaluating FilterExpression."""
        evaluator = Evaluator()
        ds = create_test_dataset()

        # Create a filter expression: filter series where value > 102
        base = datetime(2024, 1, 1, tzinfo=UTC)
        values_series = Series[Price](
            timestamps=tuple(base + timedelta(hours=i) for i in range(10)),
            values=tuple(Price(Decimal(100 + i)) for i in range(10)),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        condition_series = Series[bool](
            timestamps=values_series.timestamps,
            values=tuple(v > Price(Decimal("102")) for v in values_series.values),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        filter_expr = FilterNode(series=LiteralNode(values_series), condition=LiteralNode(condition_series))
        result = _extract_single_series(evaluator.evaluate(Expression(filter_expr), ds))

        assert isinstance(result, Series)
        assert len(result.values) < len(values_series.values)  # Filtered should be shorter
        assert all(v > Price(Decimal("102")) for v in result.values)

    def test_evaluate_aggregate_expression(self):
        """Test evaluating AggregateExpression."""
        evaluator = Evaluator()
        ds = create_test_dataset()

        # Create aggregate expression: sum of series
        base = datetime(2024, 1, 1, tzinfo=UTC)
        values_series = Series[Price](
            timestamps=tuple(base + timedelta(hours=i) for i in range(10)),
            values=tuple(Price(Decimal(100 + i)) for i in range(10)),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        aggregate_expr = AggregateNode(series=LiteralNode(values_series), operation="sum", field=None)
        result = _extract_single_series(evaluator.evaluate(Expression(aggregate_expr), ds))

        assert isinstance(result, Series)
        # Sum should return a single value
        assert len(result.values) == 1

    def test_evaluate_time_shift_expression(self):
        """Test evaluating TimeShiftExpression."""
        evaluator = Evaluator()
        ds = create_test_dataset()

        # Create time shift expression: shift by 1 period
        base = datetime(2024, 1, 1, tzinfo=UTC)
        values_series = Series[Price](
            timestamps=tuple(base + timedelta(hours=i) for i in range(10)),
            values=tuple(Price(Decimal(100 + i)) for i in range(10)),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        shift_expr = TimeShiftNode(series=LiteralNode(values_series), shift="1h_ago", operation=None)
        result = _extract_single_series(evaluator.evaluate(Expression(shift_expr), ds))

        assert isinstance(result, Series)
        assert len(result.values) > 0

    def test_evaluate_time_shift_with_change(self):
        """Test evaluating TimeShiftExpression with change operation."""
        evaluator = Evaluator()
        ds = create_test_dataset()

        # Create time shift expression with change operation
        base = datetime(2024, 1, 1, tzinfo=UTC)
        values_series = Series[Price](
            timestamps=tuple(base + timedelta(hours=i) for i in range(10)),
            values=tuple(Price(Decimal(100 + i)) for i in range(10)),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        shift_expr = TimeShiftNode(series=LiteralNode(values_series), shift="1h", operation="change")
        result = _extract_single_series(evaluator.evaluate(Expression(shift_expr), ds))

        assert isinstance(result, Series)
        assert len(result.values) > 0

    def test_cache_functionality(self):
        """Test that caching works correctly."""
        evaluator = Evaluator()
        ds = create_test_dataset()

        expr = compile_expression("sma(BTC.price, period=5)")

        result1 = _extract_single_series(evaluator.evaluate(expr, ds))
        cache_size1 = len(evaluator._cache)

        result2 = _extract_single_series(evaluator.evaluate(expr, ds))
        cache_size2 = len(evaluator._cache)

        # Results should be the same
        assert result1.values == result2.values

        assert cache_size1 > 0
        assert cache_size2 > 0
        evaluator._cache.clear()
        assert len(evaluator._cache) == 0

    def test_evaluate_empty_dataset(self):
        """Test evaluating with empty dataset."""
        evaluator = Evaluator()
        ds = Dataset()

        expr = compile_expression("BTC.price > 100")
        result = evaluator.evaluate(expr, ds)
        assert isinstance(result, dict)
        assert result == {}

    def test_parse_shift_periods(self):
        """Test parsing shift period strings."""
        assert parse_shift_periods("1h_ago") == 1
        assert parse_shift_periods("24h_ago") == 24
        assert parse_shift_periods("1h") == 1
        assert parse_shift_periods("1") == 1
        with pytest.raises(ValueError):
            parse_shift_periods("invalid")

    def test_evaluate_with_trades_source(self):
        """Test evaluating expression with trades source."""
        evaluator = Evaluator()
        ds = create_test_dataset()

        # Add trades series
        base = datetime(2024, 1, 1, tzinfo=UTC)
        trades_series = Series[Price](
            timestamps=tuple(base + timedelta(hours=i) for i in range(10)),
            values=tuple(Price(Decimal(1000 + i * 100)) for i in range(10)),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        ds.add_trade_series("BTCUSDT", "1h", trades_series)

        expr = compile_expression("sma(BTC.trades.volume, period=5)")
        result = _extract_single_series(evaluator.evaluate(expr, ds))

        assert isinstance(result, Series)
        assert len(result.values) > 0
