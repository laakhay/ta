"""Shared node-level step adapters for execution backends."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ...core.series import Series
from ..ir.nodes import BinaryOpNode, LiteralNode, SourceRefNode


def eval_source_ref_step(node: SourceRefNode, tick: dict[str, Any]) -> Decimal | None:
    """Evaluate a source reference for one tick update."""
    key1 = f"{node.source}.{node.field}"
    key2 = node.field
    if key1 in tick:
        return Decimal(str(tick[key1]))
    if key2 in tick:
        return Decimal(str(tick[key2]))
    return None


def eval_literal_step(node: LiteralNode) -> Any:
    """Evaluate a literal for one tick update."""
    if isinstance(node.value, Series) and len(node.value) == 1:
        return Decimal(str(node.value.values[0]))
    if isinstance(node.value, str):
        return node.value
    return Decimal(str(node.value)) if node.value is not None else None


def eval_binary_step(node: BinaryOpNode, children_vals: list[Any]) -> Any:
    """Evaluate a binary operator for one tick update."""
    if len(children_vals) < 2 or children_vals[0] is None or children_vals[1] is None:
        return None
    left, right = children_vals[0], children_vals[1]
    op = node.operator
    if op == "add":
        return left + right
    if op == "sub":
        return left - right
    if op == "mul":
        return left * right
    if op == "div":
        return left / right if right != 0 else Decimal(0)
    if op == "eq":
        return Decimal(1) if left == right else Decimal(0)
    if op == "gt":
        return Decimal(1) if left > right else Decimal(0)
    if op == "lt":
        return Decimal(1) if left < right else Decimal(0)
    return None
