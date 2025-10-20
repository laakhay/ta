"""Operator overloading for Series to enable expression building."""

from __future__ import annotations

from typing import Any

from ..core import Series
from .models import BinaryOp, ExpressionNode, Literal, OperatorType, UnaryOp


class Expression:
    """Expression wrapper that enables operator overloading for Series objects."""

    def __init__(self, node: ExpressionNode):
        """Initialize expression with a node."""
        self._node = node

    def __add__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Addition operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.ADD, self._node, other_node))

    def __sub__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Subtraction operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.SUB, self._node, other_node))

    def __mul__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Multiplication operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MUL, self._node, other_node))

    def __truediv__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Division operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.DIV, self._node, other_node))

    def __mod__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Modulo operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MOD, self._node, other_node))

    def __pow__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Power operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.POW, self._node, other_node))

    def __eq__(self, other: Expression | Series[Any] | float | int) -> Expression:  # type: ignore[override]
        """Equality operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.EQ, self._node, other_node))

    def __ne__(self, other: Expression | Series[Any] | float | int) -> Expression:  # type: ignore[override]
        """Inequality operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.NE, self._node, other_node))

    def __lt__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Less than operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.LT, self._node, other_node))

    def __le__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Less than or equal operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.LE, self._node, other_node))

    def __gt__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Greater than operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.GT, self._node, other_node))

    def __ge__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Greater than or equal operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.GE, self._node, other_node))

    def __neg__(self) -> Expression:
        """Unary negation operator."""
        return Expression(UnaryOp(OperatorType.NEG, self._node))

    def __pos__(self) -> Expression:
        """Unary plus operator."""
        return Expression(UnaryOp(OperatorType.POS, self._node))

    def __and__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Bitwise AND operator (logical AND)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.AND, self._node, other_node))

    def __or__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Bitwise OR operator (logical OR)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.OR, self._node, other_node))

    def __invert__(self) -> Expression:
        """Bitwise NOT operator (logical NOT)."""
        return Expression(UnaryOp(OperatorType.NOT, self._node))

    # Reverse operations for numeric literals
    def __radd__(self, other: float | int) -> Expression:
        """Reverse addition operator (other + self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.ADD, other_node, self._node))

    def __rsub__(self, other: float | int) -> Expression:
        """Reverse subtraction operator (other - self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.SUB, other_node, self._node))

    def __rmul__(self, other: float | int) -> Expression:
        """Reverse multiplication operator (other * self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MUL, other_node, self._node))

    def __rtruediv__(self, other: float | int) -> Expression:
        """Reverse division operator (other / self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.DIV, other_node, self._node))

    def __rmod__(self, other: float | int) -> Expression:
        """Reverse modulo operator (other % self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MOD, other_node, self._node))

    def __rpow__(self, other: float | int) -> Expression:
        """Reverse power operator (other ** self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.POW, other_node, self._node))

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:
        """Evaluate the expression with given context."""
        return self._node.evaluate(context)

    def dependencies(self) -> list[str]:
        """Get list of dependencies this expression requires."""
        return self._node.dependencies()

    def describe(self) -> str:
        """Get human-readable description of this expression."""
        return self._node.describe()


def _to_node(value: Expression | ExpressionNode | Series[Any] | float | int) -> ExpressionNode:
    """Convert a value to an ExpressionNode."""
    if isinstance(value, Expression):
        return value._node  # type: ignore[misc]
    elif isinstance(value, ExpressionNode):
        return value
    else:
        return Literal(value)


def as_expression(series: Series[Any]) -> Expression:
    """Convert a Series to an Expression for operator overloading."""
    return Expression(Literal(series))
