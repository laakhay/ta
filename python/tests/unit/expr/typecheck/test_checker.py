"""Tests for Static Type Checking."""

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.expr.ir.nodes import (
    AggregateNode,
    BinaryOpNode,
    CallNode,
    FilterNode,
    LiteralNode,
    SourceRefNode,
    TimeShiftNode,
    UnaryOpNode,
)
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


def test_negative_period():
    """Test error for negative period."""
    close = SourceRefNode(symbol="BTC", field="close")
    # rsi period must be positive
    expr = CallNode("test_rsi", args=[close, LiteralNode(-5)])
    with pytest.raises(TypeCheckError, match="must be positive"):
        typecheck_expression(expr)


def test_filter_node_validation():
    """Test validation for FilterNode."""
    trades = SourceRefNode(symbol="BTC", source="trades", field="price")

    # Valid filter: trades where price > 50000
    cond = BinaryOpNode("gt", trades, LiteralNode(50000.0))
    expr = FilterNode(series=trades, condition=cond)
    assert typecheck_expression(expr) == expr

    # Invalid filter: condition is a string literal (non-boolean)
    invalid_expr = FilterNode(series=trades, condition=LiteralNode("high"))
    with pytest.raises(TypeCheckError, match="Condition must be boolean"):
        typecheck_expression(invalid_expr)

    # Invalid filter: condition uses non-boolean operator
    invalid_cond = BinaryOpNode("add", trades, LiteralNode(1.0))
    invalid_expr2 = FilterNode(series=trades, condition=invalid_cond)
    with pytest.raises(TypeCheckError, match="Condition uses non-boolean operator"):
        typecheck_expression(invalid_expr2)


def test_aggregate_node_validation():
    """Test validation for AggregateNode."""
    trades = SourceRefNode(symbol="BTC", source="trades", field="price")

    # Valid aggregate: sum of amount in trades
    expr = AggregateNode(series=trades, operation="sum", field="amount")
    assert typecheck_expression(expr) == expr

    # Invalid operation
    with pytest.raises(TypeCheckError, match="Unknown operation"):
        typecheck_expression(AggregateNode(series=trades, operation="unknown"))

    # Invalid field for trades
    with pytest.raises(TypeCheckError, match="Field 'invalid' is not valid for source 'trades'"):
        typecheck_expression(AggregateNode(series=trades, operation="sum", field="invalid"))

    # Invalid field for ohlcv
    close = SourceRefNode(symbol="BTC", field="close")
    with pytest.raises(TypeCheckError, match="Field 'amount' is not valid for source 'ohlcv'"):
        typecheck_expression(AggregateNode(series=close, operation="avg", field="amount"))


def test_timeshift_node_validation():
    """Test validation for TimeShiftNode."""
    close = SourceRefNode(symbol="BTC", field="close")

    # Valid shift
    expr = TimeShiftNode(series=close, shift="24h")
    assert typecheck_expression(expr) == expr

    # Missing shift
    with pytest.raises(TypeCheckError, match="Missing shift value"):
        typecheck_expression(TimeShiftNode(series=close, shift=""))


def test_recursive_new_nodes():
    """Test recursive validation for new node types."""
    close = SourceRefNode(symbol="BTC", field="close")
    invalid_inner = CallNode("test_sma", args=[LiteralNode(100)])  # Invalid

    # Filter with invalid inner
    with pytest.raises(TypeCheckError, match="expects a Series"):
        typecheck_expression(FilterNode(series=invalid_inner, condition=LiteralNode(True)))

    # Aggregate with invalid inner
    with pytest.raises(TypeCheckError, match="expects a Series"):
        typecheck_expression(AggregateNode(series=invalid_inner, operation="sum"))
