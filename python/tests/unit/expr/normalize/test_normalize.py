"""Tests for expression normalization and constant folding."""

from laakhay.ta.expr.ir.nodes import BinaryOpNode, CallNode, LiteralNode, SourceRefNode, UnaryOpNode
from laakhay.ta.expr.normalize.normalize import normalize_expression


def test_constant_folding_arithmetic():
    """Test folding of simple arithmetic operations."""
    # 1 + 2 * 3 -> 7
    inner_mul = BinaryOpNode("mul", LiteralNode(2), LiteralNode(3))
    root = BinaryOpNode("add", LiteralNode(1), inner_mul)

    normalized = normalize_expression(root)
    assert isinstance(normalized, LiteralNode)
    assert normalized.value == 7


def test_constant_folding_logical():
    """Test folding of logical operations."""
    # not (True and False) -> True
    inner_and = BinaryOpNode("and", LiteralNode(True), LiteralNode(False))
    root = UnaryOpNode("not", inner_and)

    normalized = normalize_expression(root)
    assert isinstance(normalized, LiteralNode)
    assert normalized.value is True


def test_identity_normalization_and():
    """Test identity normalization for 'and'."""
    # True and x -> x
    # False and x -> False
    source = SourceRefNode(symbol="BTC", field="close")

    # True and x
    expr1 = BinaryOpNode("and", LiteralNode(True), source)
    assert normalize_expression(expr1) == source

    # x and True
    expr2 = BinaryOpNode("and", source, LiteralNode(True))
    assert normalize_expression(expr2) == source

    # False and x
    expr3 = BinaryOpNode("and", LiteralNode(False), source)
    norm3 = normalize_expression(expr3)
    assert isinstance(norm3, LiteralNode)
    assert norm3.value is False


def test_identity_normalization_or():
    """Test identity normalization for 'or'."""
    # False or x -> x
    # True or x -> True
    source = SourceRefNode(symbol="BTC", field="close")

    # False or x
    expr1 = BinaryOpNode("or", LiteralNode(False), source)
    assert normalize_expression(expr1) == source

    # x or False
    expr2 = BinaryOpNode("or", source, LiteralNode(False))
    assert normalize_expression(expr2) == source

    # True or x
    expr3 = BinaryOpNode("or", LiteralNode(True), source)
    norm3 = normalize_expression(expr3)
    assert isinstance(norm3, LiteralNode)
    assert norm3.value is True


def test_source_canonicalization():
    """Test mapping 'price' to 'close'."""
    source = SourceRefNode(symbol="BTC", field="price")
    normalized = normalize_expression(source)
    assert normalized.field == "close"


def test_nested_normalization():
    """Test normalization inside CallNode arguments."""
    # sma(close, 5 + 5) -> sma(close, 10)
    source = SourceRefNode(symbol="BTC", field="close")
    period_expr = BinaryOpNode("add", LiteralNode(5), LiteralNode(5))
    root = CallNode(name="sma", args=[source, period_expr])

    normalized = normalize_expression(root)
    assert isinstance(normalized, CallNode)
    assert len(normalized.args) == 2
    assert isinstance(normalized.args[1], LiteralNode)
    assert normalized.args[1].value == 10


def test_division_by_zero_no_folding():
    """Test that division by zero does not crash and does not fold."""
    root = BinaryOpNode("div", LiteralNode(10), LiteralNode(0))
    normalized = normalize_expression(root)
    # Should stay as-is if folding fails
    assert isinstance(normalized, BinaryOpNode)
    assert normalized.operator == "div"
