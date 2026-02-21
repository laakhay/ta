"""Tests for RuntimeEvaluator."""

from datetime import UTC, datetime, timedelta

UTC = UTC
from decimal import Decimal

import pytest

from laakhay.ta.core.bar import Bar
from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.ir.nodes import (
    AggregateNode,
    FilterNode,
    LiteralNode,
    SourceRefNode,
    TimeShiftNode,
)
from laakhay.ta.expr.planner import plan_expression
from laakhay.ta.expr.runtime.evaluator import RuntimeEvaluator


def create_test_dataset() -> Dataset:
    """Create a test dataset with OHLCV data."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    bars = [
        Bar.from_raw(base + timedelta(hours=i), 100 + i, 101 + i, 99 + i, 100 + i, 1000 + i, True) for i in range(10)
    ]
    ds = Dataset()
    ds.add_series("BTCUSDT", "1h", OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h"))
    return ds


class TestRuntimeEvaluator:
    """Test RuntimeEvaluator functionality."""

    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        evaluator = RuntimeEvaluator()
        assert evaluator._cache == {}
        assert evaluator.get_cache_stats()["cache_size"] == 0

    def test_evaluate_simple_expression(self):
        """Test evaluating a simple expression."""
        evaluator = RuntimeEvaluator()
        ds = create_test_dataset()

        # Compile and plan expression
        expr = compile_expression("BTC.price > 100")
        plan = plan_expression(expr._node)

        # Evaluate
        result = evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"
        assert len(result.values) > 0

    def test_evaluate_with_indicator(self):
        """Test evaluating expression with indicator."""
        evaluator = RuntimeEvaluator()
        ds = create_test_dataset()

        # Compile and plan expression
        expr = compile_expression("sma(BTC.price, period=5)")
        plan = plan_expression(expr._node)

        # Evaluate
        result = evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"
        assert len(result.values) > 0

    def test_evaluate_multi_symbol_timeframe(self):
        """Test evaluating for multiple symbol/timeframe combinations."""
        evaluator = RuntimeEvaluator()
        ds = create_test_dataset()

        # Add another symbol
        base = datetime(2024, 1, 1, tzinfo=UTC)
        eth_bars = [
            Bar.from_raw(base + timedelta(hours=i), 200 + i, 201 + i, 199 + i, 200 + i, 2000 + i, True)
            for i in range(10)
        ]
        ds.add_series("ETHUSDT", "1h", OHLCV.from_bars(eth_bars, symbol="ETHUSDT", timeframe="1h"))

        # Compile and plan expression
        expr = compile_expression("BTC.price > 100")
        plan = plan_expression(expr._node)

        # Evaluate for all symbols
        results = evaluator.evaluate(plan, ds)

        assert isinstance(results, dict)
        assert ("BTCUSDT", "1h", "default") in results
        assert ("ETHUSDT", "1h", "default") in results

    def test_evaluate_source_expression(self):
        """Test evaluating SourceExpression."""
        evaluator = RuntimeEvaluator()
        ds = create_test_dataset()

        # Create SourceRefNode directly
        source_expr = SourceRefNode(
            symbol="BTCUSDT",
            field="price",
            exchange=None,
            timeframe="1h",
            source="ohlcv",
        )

        # Plan it (wrap in a simple plan)
        from laakhay.ta.expr.planner.builder import build_graph
        from laakhay.ta.expr.planner.planner import compute_plan

        graph = build_graph(source_expr)
        plan = compute_plan(graph)

        # Evaluate
        result = evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"
        assert len(result.values) == 10

    def test_evaluate_filter_expression(self):
        """Test evaluating FilterExpression."""
        evaluator = RuntimeEvaluator()
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

        # Plan it
        from laakhay.ta.expr.planner.builder import build_graph
        from laakhay.ta.expr.planner.planner import compute_plan

        graph = build_graph(filter_expr)
        plan = compute_plan(graph)

        # Evaluate
        result = evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result, Series)
        assert len(result.values) < len(values_series.values)  # Filtered should be shorter
        assert all(v > Price(Decimal("102")) for v in result.values)

    def test_evaluate_aggregate_expression(self):
        """Test evaluating AggregateExpression."""
        evaluator = RuntimeEvaluator()
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

        # Plan it
        from laakhay.ta.expr.planner.builder import build_graph
        from laakhay.ta.expr.planner.planner import compute_plan

        graph = build_graph(aggregate_expr)
        plan = compute_plan(graph)

        # Evaluate
        result = evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result, Series)
        # Sum should return a single value
        assert len(result.values) == 1

    def test_evaluate_time_shift_expression(self):
        """Test evaluating TimeShiftExpression."""
        evaluator = RuntimeEvaluator()
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

        # Plan it
        from laakhay.ta.expr.planner.builder import build_graph
        from laakhay.ta.expr.planner.planner import compute_plan

        graph = build_graph(shift_expr)
        plan = compute_plan(graph)

        # Evaluate
        result = evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result, Series)
        assert len(result.values) > 0

    def test_evaluate_time_shift_with_change(self):
        """Test evaluating TimeShiftExpression with change operation."""
        evaluator = RuntimeEvaluator()
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

        # Plan it
        from laakhay.ta.expr.planner.builder import build_graph
        from laakhay.ta.expr.planner.planner import compute_plan

        graph = build_graph(shift_expr)
        plan = compute_plan(graph)

        # Evaluate
        result = evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result, Series)
        assert len(result.values) > 0

    def test_cache_functionality(self):
        """Test that caching works correctly."""
        evaluator = RuntimeEvaluator()
        ds = create_test_dataset()

        # Compile and plan expression
        expr = compile_expression("sma(BTC.price, period=5)")
        plan = plan_expression(expr._node)

        # First evaluation - should populate cache
        result1 = evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")
        cache_stats1 = evaluator.get_cache_stats()

        # Second evaluation - should use cache
        result2 = evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")
        cache_stats2 = evaluator.get_cache_stats()

        # Results should be the same
        assert result1.values == result2.values

        # Cache should have entries
        assert cache_stats2["cache_size"] > 0

        # Clear cache
        evaluator.clear_cache()
        cache_stats3 = evaluator.get_cache_stats()
        assert cache_stats3["cache_size"] == 0

    def test_evaluate_empty_dataset(self):
        """Test evaluating with empty dataset."""
        evaluator = RuntimeEvaluator()
        ds = Dataset()

        expr = compile_expression("BTC.price > 100")
        plan = plan_expression(expr._node)

        result = evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        # Should return empty series
        assert isinstance(result, Series)
        assert len(result.values) == 0

    def test_parse_shift_periods(self):
        """Test parsing shift period strings."""
        evaluator = RuntimeEvaluator()

        assert evaluator._parse_shift_periods("1h_ago") == 1
        assert evaluator._parse_shift_periods("24h_ago") == 24
        assert evaluator._parse_shift_periods("1h") == 1
        assert evaluator._parse_shift_periods("1") == 1

        from laakhay.ta.exceptions import EvaluationError

        with pytest.raises(EvaluationError, match="Invalid shift format"):
            evaluator._parse_shift_periods("invalid")

    def test_evaluate_with_trades_source(self):
        """Test evaluating expression with trades source."""
        evaluator = RuntimeEvaluator()
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

        # Compile expression that uses trades
        expr = compile_expression("sma(BTC.trades.volume, period=5)")
        plan = plan_expression(expr._node)

        # Evaluate
        result = evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result, Series)
        assert len(result.values) > 0
