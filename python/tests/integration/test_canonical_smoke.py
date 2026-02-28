"""Integration smoke tests for the Canonical IR compilation pipeline.

These tests verify the interplay between Parser -> Normalizer -> Typechecker
using complex, real-world strategy expressions.
"""

import pytest

from laakhay.ta.expr.compile import compile_to_ir
from laakhay.ta.expr.ir.nodes import (
    AggregateNode,
    BinaryOpNode,
    CallNode,
    FilterNode,
    SourceRefNode,
)

# A collection of 30 "real-world" style strings to stress test the pipeline
SMOKE_TEST_EXPRESSIONS = [
    # 1-5: Basic Indicators & Normalization
    "sma(close, 20)",
    "rsi(close, 14) > 70",
    "ema(close, 10) > ema(close, 20)",
    "sma(close, 5 + 5)",  # Constant folding
    "rsi(price, 14)",  # Field canonicalization (price -> close)
    # 6-10: Logic & Unary Ops
    "ema(close, 10) > ema(close, 20) and rsi(close, 14) < 30",
    "not (close > open)",
    "sma(rsi(close, 14), 20)",  # Nested indicators
    "trades.sum(amount)",
    "trades.filter(amount > 1000).sum(price)",
    # 11-15: Arithmetic & Aggregations
    "(high - low) / (high + low) * 100",
    "close > sma(close, 20) and close < sma(close, 10)",
    "atr(14) * 2 + close",
    "trades.avg(price) > ohlcv.close",
    "sma(close, period=50)",
    # 16-20: Deep Nesting & Outputs
    "ema(sma(rsi(close, 14), 9), 21)",
    "(close > open) and (volume > 1000)",  # Simple multi-condition
    "bbands(close, 20).upper > close",
    "macd(close, 12, 26, 9).signal > 0",
    "stochastic(14, 3).k < 20",
    # 21-25: Advanced Logic & Patterns
    "typical_price > sma(typical_price, 20)",
    "(high + low + close) / 3",
    "hlc3 > sma(hlc3, 10)",
    "trades.filter(amount > 100).sum(amount) > 1000",
    "rsi(close, 14) > 50 or (close > ema(close, 200) and volume > sma(volume, 20))",
    # 26-30: Mathematical Formulas & Volatility
    "((close - low) - (high - close)) / (high - low) * volume",
    "sma(close, 20) + 2 * rolling_std(close, 20)",
    "abs(close - open) / atr(14)",
    "(close - sma(close, 20)) / sma(close, 20) * 100",
    "ohlcv.filter(volume > 1000).count()",
]


@pytest.mark.parametrize("expr_text", SMOKE_TEST_EXPRESSIONS)
def test_compile_smoke_suite(expr_text):
    """Verify that complex expressions pass through the full pipeline without error."""
    # This triggers Parse -> Normalize -> Typecheck
    try:
        ir = compile_to_ir(expr_text)
    except Exception as e:
        pytest.fail(f"Failed to compile '{expr_text}': {e}")

    # Structural verification: IR must not be None
    assert ir is not None

    # We should also be able to serialize it (Phase 8 verification)
    from laakhay.ta.expr.ir.serialize import ir_from_dict, ir_to_dict

    data = ir_to_dict(ir)
    reconstructed = ir_from_dict(data)
    assert reconstructed == ir


def test_specific_folding_integration():
    """Verify integration of folding and field mapping in a complex case."""
    # 'price' should map to 'close'
    # '10 + 10' should fold to '20'
    text = "sma(price, 10 + 10) > 50"
    ir = compile_to_ir(text)

    # Structure should be: BinaryOpNode(gt, CallNode(sma, [SourceRef(close), Literal(20)]), Literal(50))
    assert isinstance(ir, BinaryOpNode)
    assert ir.operator == "gt"

    left = ir.left
    assert isinstance(left, CallNode)
    assert left.name == "sma"

    # Period should be folded
    # args[0] is close, args[1] is 20
    assert left.args[1].value == 20

    # Source should be canonicalized
    source = left.args[0]
    assert isinstance(source, SourceRefNode)
    assert source.field == "close"


def test_filter_aggregate_integration():
    """Verify integration of filter/aggregate hardening."""
    text = "trades.filter(amount > 100).sum(price)"
    ir = compile_to_ir(text)

    assert isinstance(ir, AggregateNode)
    assert ir.operation == "sum"
    assert ir.field == "price"

    series = ir.series
    assert isinstance(series, FilterNode)
    assert series.series.source == "trades"
    assert isinstance(series.condition, BinaryOpNode)


def test_invalid_integration_cases():
    """Verify that errors are still caught at the end of the pipeline."""
    from laakhay.ta.expr.typecheck.checker import TypeCheckError

    # Invalid period (Negative) - caught by TypeChecker
    with pytest.raises(TypeCheckError):
        compile_to_ir("sma(close, -5)")

    # Invalid filter (non-boolean) - caught by TypeChecker
    with pytest.raises(TypeCheckError, match="Condition must be boolean"):
        compile_to_ir("trades.filter(100)")

    # Invalid field for trades - caught by TypeChecker
    with pytest.raises(TypeCheckError, match="is not valid for source 'trades'"):
        compile_to_ir("trades.sum('invalid')")
