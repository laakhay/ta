"""Expression system for technical analysis computations."""

from __future__ import annotations

from enum import Enum
from typing import Any

from ..ir.nodes import (
    AggregateNode,
    BinaryOpNode,
    FilterNode,
    LiteralNode,
    SourceRefNode,
    TimeShiftNode,
    UnaryOpNode,
)
from . import alignment
from .alignment import alignment as alignment_func
from .alignment import get_policy
from .operators import Expression, as_expression


class OperatorType(str, Enum):
    """Legacy operator enum kept for backward compatibility."""

    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    POW = "pow"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EQ = "eq"
    NEQ = "neq"
    AND = "and"
    OR = "or"
    NOT = "not"
    NEG = "neg"
    POS = "pos"


_IR_NODE_NAMES = {
    "LiteralNode",
    "SourceRefNode",
    "CallNode",
    "BinaryOpNode",
    "UnaryOpNode",
    "FilterNode",
    "AggregateNode",
    "TimeShiftNode",
    "MemberAccessNode",
    "IndexNode",
}


def _to_node(value: Any) -> Any:
    if isinstance(value, Expression):
        return value._node  # type: ignore[attr-defined]
    if hasattr(value, "_to_expression"):
        try:
            expr = value._to_expression()
            if isinstance(expr, Expression):
                return expr._node  # type: ignore[attr-defined]
        except Exception:
            pass
    if type(value).__name__ in _IR_NODE_NAMES:
        return value
    return LiteralNode(value)


def Literal(value: Any) -> LiteralNode:
    """Legacy constructor alias for LiteralNode."""
    return LiteralNode(value)


def BinaryOp(operator: OperatorType | str, left: Any, right: Any) -> BinaryOpNode:
    """Legacy constructor alias for BinaryOpNode."""
    op = operator.value if isinstance(operator, OperatorType) else str(operator).lower()
    return BinaryOpNode(op, _to_node(left), _to_node(right))


def UnaryOp(operator: OperatorType | str, operand: Any) -> UnaryOpNode:
    """Legacy constructor alias for UnaryOpNode."""
    op = operator.value if isinstance(operator, OperatorType) else str(operator).lower()
    return UnaryOpNode(op, _to_node(operand))


__all__ = [
    "OperatorType",
    "BinaryOp",
    "UnaryOp",
    "Literal",
    "BinaryOpNode",
    "UnaryOpNode",
    "LiteralNode",
    "SourceRefNode",
    "FilterNode",
    "AggregateNode",
    "TimeShiftNode",
    "Expression",
    "as_expression",
    "alignment",
    "alignment_func",
    "get_policy",
]
