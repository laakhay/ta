"""Tests for IR typechecker."""

from laakhay.ta.expr.ir.nodes import LiteralNode
from laakhay.ta.expr.typecheck.checker import typecheck_expression


def test_typecheck_identity():
    """Currently typecheck is an identity placeholder."""
    node = LiteralNode(value=42.0)
    assert typecheck_expression(node) is node
