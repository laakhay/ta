"""Drift guard tests: ensure Expression.run and evaluate_plan paths produce identical results.

These tests verify that the canonical execution path (runner -> backend) stays in sync
with direct Evaluator usage, and that batch vs incremental backends produce parity.
See ta/plans/ta-legacy-cleanup-dedup-plan.md Phase 0.
"""

import pytest

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.execution import evaluate_plan
from laakhay.ta.expr.execution.backends.batch import BatchBackend
from laakhay.ta.expr.execution.backends.incremental_rust import IncrementalRustBackend
from laakhay.ta.expr.planner.evaluator import Evaluator
from tests.parity.utils import assert_dict_parity, assert_series_parity


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


@pytest.mark.parametrize(
    "expr_text",
    [
        "sma(close, 14)",
        "close * 2",
    ],
)
def test_batch_vs_incremental_backend_parity(sample_dataset, expr_text):
    """Batch and Rust incremental backends must match."""
    expr = compile_expression(expr_text)
    plan = expr._ensure_plan()

    batch_res = BatchBackend().evaluate(plan, sample_dataset)
    rust_incr_res = IncrementalRustBackend().evaluate(plan, sample_dataset)

    if isinstance(batch_res, dict):
        assert_dict_parity(batch_res, rust_incr_res)
    else:
        assert_series_parity(batch_res, rust_incr_res)


def test_evaluator_direct_vs_run_parity(sample_dataset):
    """Direct Evaluator.evaluate(Dataset) and Expression.run(Dataset) must agree."""
    expr = compile_expression("close + 10")

    eval_result = Evaluator().evaluate(expr, sample_dataset)
    run_result = expr.run(sample_dataset)

    r1 = _extract_series(eval_result)
    r2 = _extract_series(run_result)
    assert_series_parity(r1, r2)
