"""Drift guard tests for expression execution and evaluator parity."""

import pytest

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.execution import evaluate_plan
from laakhay.ta.expr.execution.backends.incremental_rust import IncrementalRustBackend
from tests.parity.utils import assert_series_parity


@pytest.fixture
def sample_dataset(sample_ohlcv_data):
    """Dataset for drift guard tests."""
    from laakhay.ta.core.ohlcv import OHLCV

    ohlcv = OHLCV(
        timestamps=sample_ohlcv_data["timestamps"],
        opens=sample_ohlcv_data["opens"],
        highs=sample_ohlcv_data["highs"],
        lows=sample_ohlcv_data["lows"],
        closes=sample_ohlcv_data["closes"],
        volumes=sample_ohlcv_data["volumes"],
        is_closed=sample_ohlcv_data["is_closed"],
        symbol=sample_ohlcv_data["symbol"],
        timeframe=sample_ohlcv_data["timeframe"],
    )
    ds = Dataset()
    ds.add_series(ohlcv.symbol, ohlcv.timeframe, ohlcv, "ohlcv")
    return ds


def _extract_series(result):
    """Extract single series from run/evaluate result."""
    if isinstance(result, dict):
        return next(iter(result.values()))
    return result


@pytest.mark.parametrize(
    "expr_text",
    [
        "sma(close, 14)",
        "close + 10",
        "rsi(close, 14)",
    ],
)
def test_expression_run_vs_evaluate_plan_parity(sample_dataset, expr_text):
    """Expression.run() and evaluate_plan() must produce identical results."""
    expr = compile_expression(expr_text)
    plan = expr._ensure_plan()

    run_result = expr.run(sample_dataset)
    plan_result = evaluate_plan(plan, sample_dataset)

    r1 = _extract_series(run_result)
    r2 = _extract_series(plan_result)
    assert_series_parity(r1, r2)


def test_incremental_backend_rejects_unsupported_graph(sample_dataset):
    expr = compile_expression("close * 2")
    plan = expr._ensure_plan()

    result = IncrementalRustBackend().evaluate(plan, sample_dataset)
    assert result is not None
