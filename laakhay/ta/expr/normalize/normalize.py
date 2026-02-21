"""Normalization of strategy expression IR.

Passes over the CanonicalExpression to perform:
- source canonicalization
- constant folding
- identity normalization
- positional -> named arg normalization
"""

from typing import Any

from ..ir.nodes import (
    BinaryOpNode,
    CallNode,
    CanonicalExpression,
    LiteralNode,
    SourceRefNode,
    UnaryOpNode,
)


def normalize_expression(expr: CanonicalExpression) -> CanonicalExpression:
    """Normalize a canonical expression recursively."""

    if isinstance(expr, LiteralNode):
        return expr

    if isinstance(expr, SourceRefNode):
        # Source canonicalization: price -> close
        if expr.field is not None:
            field = expr.field.lower()
            if field == "price":
                return SourceRefNode(
                symbol=expr.symbol,
                field="close",
                source=expr.source,
                exchange=expr.exchange,
                timeframe=expr.timeframe,
                base=expr.base,
                quote=expr.quote,
                instrument_type=expr.instrument_type,
                span_start=expr.span_start,
                span_end=expr.span_end,
                type_tag=expr.type_tag,
            )
        return expr

    if isinstance(expr, BinaryOpNode):
        left = normalize_expression(expr.left)
        right = normalize_expression(expr.right)

        # Constant folding
        if isinstance(left, LiteralNode) and isinstance(right, LiteralNode):
            val = _fold_binary(expr.operator, left.value, right.value)
            if val is not None:
                return LiteralNode(value=val)

        # Identity normalization
        if expr.operator == "and":
            if isinstance(left, LiteralNode) and left.value is True:
                return right
            if isinstance(right, LiteralNode) and right.value is True:
                return left
            if isinstance(left, LiteralNode) and left.value is False:
                return LiteralNode(value=False)
            if isinstance(right, LiteralNode) and right.value is False:
                return LiteralNode(value=False)

        if expr.operator == "or":
            if isinstance(left, LiteralNode) and left.value is True:
                return LiteralNode(value=True)
            if isinstance(right, LiteralNode) and right.value is True:
                return LiteralNode(value=True)
            if isinstance(left, LiteralNode) and left.value is False:
                return right
            if isinstance(right, LiteralNode) and right.value is False:
                return left

        return BinaryOpNode(
            operator=expr.operator,
            left=left,
            right=right,
            span_start=expr.span_start,
            span_end=expr.span_end,
            type_tag=expr.type_tag,
        )

    if isinstance(expr, UnaryOpNode):
        operand = normalize_expression(expr.operand)

        # Constant folding
        if isinstance(operand, LiteralNode):
            val = _fold_unary(expr.operator, operand.value)
            if val is not None:
                return LiteralNode(value=val)

        return UnaryOpNode(
            operator=expr.operator,
            operand=operand,
            span_start=expr.span_start,
            span_end=expr.span_end,
            type_tag=expr.type_tag,
        )

    if isinstance(expr, CallNode):
        args = [normalize_expression(arg) for arg in expr.args]
        kwargs = {k: normalize_expression(v) for k, v in expr.kwargs.items()}
        return CallNode(
            name=expr.name,
            args=args,
            kwargs=kwargs,
            output=expr.output,
            span_start=expr.span_start,
            span_end=expr.span_end,
            type_tag=expr.type_tag,
        )

    # Fallback for other nodes (FilterNode, AggregateNode, etc. should also be recursive if implemented)
    for attr in ("series", "condition", "expr", "index"):
        if hasattr(expr, attr):
            val = getattr(expr, attr)
            if val is not None:
                setattr(expr, attr, normalize_expression(val))

    return expr


def _fold_binary(op: str, left: Any, right: Any) -> Any:
    """Perform constant folding for binary operations."""
    try:
        if op == "add":
            return left + right
        if op == "sub":
            return left - right
        if op == "mul":
            return left * right
        if op == "div":
            return left / right if right != 0 else None
        if op == "mod":
            return left % right if right != 0 else None
        if op == "pow":
            return left**right
        if op == "gt":
            return left > right
        if op == "gte":
            return left >= right
        if op == "lt":
            return left < right
        if op == "lte":
            return left <= right
        if op == "eq":
            return left == right
        if op == "neq":
            return left != right
    except Exception:
        return None
    return None


def _fold_unary(op: str, operand: Any) -> Any:
    """Perform constant folding for unary operations."""
    try:
        if op == "neg":
            return -operand
        if op == "pos":
            return +operand
        if op == "not":
            return not operand
    except Exception:
        return None
    return None
