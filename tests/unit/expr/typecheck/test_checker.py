"""Tests for Static Type Checking."""

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.expr.ir.nodes import BinaryOpNode, CallNode, LiteralNode, SourceRefNode, UnaryOpNode
from laakhay.ta.expr.typecheck.checker import TypeCheckError, typecheck_expression
from laakhay.ta.registry.registry import SeriesContext, get_global_registry


@pytest.fixture(autouse=True)
def setup_registry():
    """Register some test indicators."""
    registry = get_global_registry()

    @registry.register
    def test_sma(ctx: SeriesContext, input_series: Series, period: int = 20) -> Series:
        return input_series

    @registry.register
    def test_rsi(ctx: SeriesContext, input_series: Series, period: int, threshold: float = 70.0) -> Series:
        return input_series

    @registry.register
    def test_multi(ctx: SeriesContext, s1: Series, s2: Series, name: str) -> Series:
        return s1


def test_valid_sma():
    """Test valid SMA expression."""
    close = SourceRefNode(symbol="BTC", field="close")
    expr = CallNode("test_sma", args=[close], kwargs={"period": LiteralNode(14)})
    assert typecheck_expression(expr) == expr


def test_unknown_indicator():
    """Test error for unknown indicator."""
    with pytest.raises(TypeCheckError, match="Unknown indicator: unknown"):
        typecheck_expression(CallNode("unknown", args=[]))


def test_missing_required_param():
    """Test error for missing required parameter."""
    # test_rsi requires 'period'
    close = SourceRefNode(symbol="BTC", field="close")
    expr = CallNode("test_rsi", args=[close])  # period missing
    with pytest.raises(TypeCheckError, match="Missing required parameter: period"):
        typecheck_expression(expr)


def test_too_many_args():
    """Test error for too many positional arguments."""
    close = SourceRefNode(symbol="BTC", field="close")
    # test_sma has 2 params: input_series, period
    expr = CallNode("test_sma", args=[close, LiteralNode(14), LiteralNode(20)])
    with pytest.raises(TypeCheckError, match="Too many positional arguments"):
        typecheck_expression(expr)


def test_type_mismatch_literal_for_series():
    """Test error when a literal is provided for a Series parameter."""
    expr = CallNode("test_sma", args=[LiteralNode(100)])  # input_series expects Series
    with pytest.raises(TypeCheckError, match="expects a Series"):
        typecheck_expression(expr)


def test_type_mismatch_scalar():
    """Test error when wrong scalar type is provided."""
    close = SourceRefNode(symbol="BTC", field="close")
    # period expects int, got str
    expr = CallNode("test_sma", args=[close, LiteralNode("twenty")])
    with pytest.raises(TypeCheckError, match="Parameter 'period' expects int, got str"):
        typecheck_expression(expr)


def test_safe_coercion_int_to_float():
    """Test that int is allowed for float parameter."""
    close = SourceRefNode(symbol="BTC", field="close")
    # threshold expects float, but 50 (int) should be okay
    expr = CallNode("test_rsi", args=[close, LiteralNode(14), LiteralNode(50)])
    assert typecheck_expression(expr) == expr


def test_positional_keyword_conflict():
    """Test error when param is specified both ways."""
    close = SourceRefNode(symbol="BTC", field="close")
    # period as 2nd arg AND as kwarg
    expr = CallNode("test_rsi", args=[close, LiteralNode(14)], kwargs={"period": LiteralNode(21)})
    with pytest.raises(TypeCheckError, match="Parameter 'period' specified both positionally and as keyword"):
        typecheck_expression(expr)


def test_recursive_typecheck():
    """Test that nested nodes are also checked."""
    close = SourceRefNode(symbol="BTC", field="close")
    # Valid outer call
    inner_invalid = CallNode("test_sma", args=[LiteralNode(100)])  # Invalid
    expr = BinaryOpNode("add", close, inner_invalid)

    with pytest.raises(TypeCheckError, match="expects a Series"):
        typecheck_expression(expr)


def test_unary_recursive():
    """Test recursive check in unary op."""
    inner_invalid = CallNode("test_sma", args=[LiteralNode(100)])  # Invalid
    expr = UnaryOpNode("neg", inner_invalid)

    with pytest.raises(TypeCheckError, match="expects a Series"):
        typecheck_expression(expr)
