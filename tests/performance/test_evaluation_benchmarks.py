"""Performance benchmarks for expression evaluation.

These benchmarks track evaluation latency to detect regressions
as the engine grows. Run with pytest-benchmark:

    pytest tests/performance/test_evaluation_benchmarks.py --benchmark-only

If pytest-benchmark is not installed, tests will run normally without benchmarking.
"""

from datetime import timezone, datetime, timedelta
UTC = timezone.utc
from decimal import Decimal

import pytest

from laakhay.ta.core.bar import Bar
from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.planner import plan_expression
from laakhay.ta.expr.runtime import RuntimeEvaluator

# Try to import pytest-benchmark, fall back to None if not available
try:
    import importlib.util

    spec = importlib.util.find_spec("pytest_benchmark")
    HAS_BENCHMARK = spec is not None
except ImportError:
    HAS_BENCHMARK = False


def create_large_dataset(size: int = 1000) -> Dataset:
    """Create a large dataset for benchmarking."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    bars = [
        Bar.from_raw(
            base + timedelta(hours=i), 100 + i * 0.1, 101 + i * 0.1, 99 + i * 0.1, 100 + i * 0.1, 1000 + i * 10, True
        )
        for i in range(size)
    ]
    ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")

    ds = Dataset()
    ds.add_series("BTCUSDT", "1h", ohlcv)
    return ds


class TestEvaluationBenchmarks:
    """Performance benchmarks for expression evaluation."""

    @pytest.fixture
    def benchmark(self, request):
        """Benchmark fixture that works with or without pytest-benchmark."""
        if HAS_BENCHMARK:
            # Use pytest-benchmark if available
            return request.getfixturevalue("benchmark")
        else:
            # Fallback: just call the function without benchmarking
            class SimpleBenchmark:
                def __call__(self, func):
                    return func()

            return SimpleBenchmark()

    def test_simple_indicator_benchmark(self, benchmark):
        """Benchmark simple indicator evaluation."""
        ds = create_large_dataset(1000)
        expr = compile_expression("sma(20)")

        def evaluate():
            return expr.run(ds)

        result = benchmark(evaluate)
        assert result is not None

    def test_complex_expression_benchmark(self, benchmark):
        """Benchmark complex expression with multiple indicators."""
        ds = create_large_dataset(1000)
        expr = compile_expression("(sma(20) > sma(50)) and (rsi(14) < 30)")

        def evaluate():
            return expr.run(ds)

        result = benchmark(evaluate)
        assert result is not None

    def test_runtime_evaluator_benchmark(self, benchmark):
        """Benchmark RuntimeEvaluator directly."""
        ds = create_large_dataset(1000)
        evaluator = RuntimeEvaluator()
        expr = compile_expression("sma(20)")
        plan = plan_expression(expr._node)

        def evaluate():
            return evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        result = benchmark(evaluate)
        assert result is not None

    def test_cached_evaluation_benchmark(self, benchmark):
        """Benchmark cached evaluation (second run should be faster)."""
        ds = create_large_dataset(1000)
        evaluator = RuntimeEvaluator()
        expr = compile_expression("sma(20)")
        plan = plan_expression(expr._node)

        # First evaluation (populates cache)
        evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        # Second evaluation (uses cache)
        def evaluate_cached():
            return evaluator.evaluate(plan, ds, symbol="BTCUSDT", timeframe="1h")

        result = benchmark(evaluate_cached)
        assert result is not None

    def test_multi_source_expression_benchmark(self, benchmark):
        """Benchmark multi-source expression evaluation."""
        ds = create_large_dataset(1000)

        # Add trades data
        base = datetime(2024, 1, 1, tzinfo=UTC)
        trades_volume = Series[Price](
            timestamps=tuple(base + timedelta(hours=i) for i in range(1000)),
            values=tuple(Price(Decimal(5000 + i * 10)) for i in range(1000)),
            symbol="BTCUSDT",
            timeframe="1h",
        )
        ds.add_trade_series("BTCUSDT", "1h", trades_volume)

        expr = compile_expression("sma(BTC.trades.volume, period=20)")

        def evaluate():
            return expr.run(ds)

        result = benchmark(evaluate)
        assert result is not None

    def test_planning_benchmark(self, benchmark):
        """Benchmark expression planning."""
        expr = compile_expression("(sma(20) > sma(50)) and (rsi(14) < 30)")

        def plan():
            return plan_expression(expr._node)

        result = benchmark(plan)
        assert result is not None
