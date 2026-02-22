"""Tests for legacy algebra constructors (Literal, BinaryOp, UnaryOp, OperatorType).

These APIs are deprecated in favor of LiteralNode, BinaryOpNode, UnaryOpNode.
See ta/docs/architecture/legacy-compat-matrix.md.
"""

import pytest

from laakhay.ta.expr.algebra import BinaryOp, Literal, OperatorType, UnaryOp
from laakhay.ta.expr.algebra.operators import Expression
from laakhay.ta.expr.ir.nodes import BinaryOpNode, LiteralNode, UnaryOpNode


@pytest.mark.legacy
class TestLegacyAlgebraConstructors:
    """Verify legacy algebra constructors still work."""

    def test_literal_constructor(self):
        """Literal(value) produces LiteralNode."""
        node = Literal(42)
        assert isinstance(node, LiteralNode)
        assert node.value == 42

    def test_binary_op_with_operator_type(self):
        """BinaryOp(OperatorType, left, right) works."""
        left = Literal(10)
        right = Literal(5)
        node = BinaryOp(OperatorType.ADD, left, right)
        assert isinstance(node, BinaryOpNode)
        assert node.operator == "add"
        assert node.left == left
        assert node.right == right

    def test_binary_op_with_string(self):
        """BinaryOp(str, left, right) works."""
        left = Literal(10)
        right = Literal(5)
        node = BinaryOp("sub", left, right)
        assert isinstance(node, BinaryOpNode)
        assert node.operator == "sub"

    def test_unary_op_constructor(self):
        """UnaryOp(operator, operand) works."""
        operand = Literal(7)
        node = UnaryOp(OperatorType.NEG, operand)
        assert isinstance(node, UnaryOpNode)
        assert node.operator == "neg"
        assert node.operand == operand

    def test_expression_from_legacy_nodes_evaluates(self, sample_dataset):
        """Expression built from legacy constructors evaluates correctly."""
        from laakhay.ta.expr.compile import compile_to_ir

        # Build equivalent: close + 10 via legacy vs canonical
        compiled = Expression(compile_to_ir("close + 10"))
        legacy_node = BinaryOp("add", compile_to_ir("close"), Literal(10))
        legacy_expr = Expression(legacy_node)

        r1 = compiled.run(sample_dataset)
        r2 = legacy_expr.run(sample_dataset)

        if isinstance(r1, dict):
            r1 = next(iter(r1.values()))
        if isinstance(r2, dict):
            r2 = next(iter(r2.values()))
        assert list(r1.values) == list(r2.values)
