"""Operator overloading for Series to enable expression building."""

from __future__ import annotations

from typing import Any, Union

from ..core import Series
from .models import ExpressionNode, Literal, BinaryOp, UnaryOp, OperatorType


class Expression:
    """Expression wrapper that enables operator overloading for Series objects."""
    
    def __init__(self, node: ExpressionNode):
        """Initialize expression with a node."""
        self._node = node
    
    def __add__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:
        """Addition operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.ADD, self._node, other_node))
    
    def __sub__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:
        """Subtraction operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.SUB, self._node, other_node))
    
    def __mul__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:
        """Multiplication operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MUL, self._node, other_node))
    
    def __truediv__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:
        """Division operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.DIV, self._node, other_node))
    
    def __mod__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:
        """Modulo operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MOD, self._node, other_node))
    
    def __pow__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:
        """Power operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.POW, self._node, other_node))
    
    def __eq__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:  # type: ignore[override]
        """Equality operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.EQ, self._node, other_node))
    
    def __ne__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:  # type: ignore[override]
        """Inequality operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.NE, self._node, other_node))
    
    def __lt__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:
        """Less than operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.LT, self._node, other_node))
    
    def __le__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:
        """Less than or equal operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.LE, self._node, other_node))
    
    def __gt__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:
        """Greater than operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.GT, self._node, other_node))
    
    def __ge__(self, other: Union[Expression, Series[Any], float, int]) -> Expression:
        """Greater than or equal operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.GE, self._node, other_node))
    
    def __neg__(self) -> Expression:
        """Unary negation operator."""
        return Expression(UnaryOp(OperatorType.NEG, self._node))
    
    def __pos__(self) -> Expression:
        """Unary plus operator."""
        return Expression(UnaryOp(OperatorType.POS, self._node))
    
    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:
        """Evaluate the expression with given context."""
        return self._node.evaluate(context)
    
    def dependencies(self) -> list[str]:
        """Get list of dependencies this expression requires."""
        return self._node.dependencies()
    
    def describe(self) -> str:
        """Get human-readable description of this expression."""
        return self._node.describe()


def _to_node(value: Union[Expression, ExpressionNode, Series[Any], float, int]) -> ExpressionNode:
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
