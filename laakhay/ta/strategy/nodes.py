"""Strategy expression node models used for parsing/analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Union, cast


class StrategyError(ValueError):
    """Base error for strategy parsing/compilation."""


@dataclass(slots=True)
class LiteralNode:
    value: float


@dataclass(slots=True)
class IndicatorNode:
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    output: str | None = None


BinaryOperator = Literal[
    "add",
    "sub",
    "mul",
    "div",
    "mod",
    "pow",
    "gt",
    "gte",
    "lt",
    "lte",
    "eq",
    "neq",
    "and",
    "or",
]


@dataclass(slots=True)
class BinaryNode:
    operator: BinaryOperator
    left: StrategyExpression
    right: StrategyExpression


UnaryOperator = Literal["not", "neg", "pos"]


@dataclass(slots=True)
class UnaryNode:
    operator: UnaryOperator
    operand: StrategyExpression


StrategyExpression = Union[LiteralNode, IndicatorNode, BinaryNode, UnaryNode]


def expression_from_dict(data: dict[str, Any]) -> StrategyExpression:
    """Recursively convert a dictionary spec to strategy nodes."""
    node_type = data.get("type")
    if node_type == "literal":
        return LiteralNode(value=float(data["value"]))
    if node_type == "indicator":
        params = cast(dict[str, Any], data.get("params") or {})
        return IndicatorNode(name=str(data["name"]).lower(), params=params, output=data.get("output"))
    if node_type == "binary":
        return BinaryNode(
            operator=cast(BinaryOperator, data["operator"]),
            left=expression_from_dict(cast(dict[str, Any], data["left"])),
            right=expression_from_dict(cast(dict[str, Any], data["right"])),
        )
    if node_type == "unary":
        return UnaryNode(
            operator=cast(UnaryOperator, data["operator"]),
            operand=expression_from_dict(cast(dict[str, Any], data["operand"])),
        )
    raise StrategyError(f"Unsupported node type '{node_type}'")


def expression_to_dict(expression: StrategyExpression) -> dict[str, Any]:
    """Convert nodes back to a dictionary representation."""
    if isinstance(expression, LiteralNode):
        return {"type": "literal", "value": expression.value}
    if isinstance(expression, IndicatorNode):
        return {"type": "indicator", "name": expression.name, "params": expression.params, "output": expression.output}
    if isinstance(expression, BinaryNode):
        return {
            "type": "binary",
            "operator": expression.operator,
            "left": expression_to_dict(expression.left),
            "right": expression_to_dict(expression.right),
        }
    if isinstance(expression, UnaryNode):
        return {
            "type": "unary",
            "operator": expression.operator,
            "operand": expression_to_dict(expression.operand),
        }
    raise StrategyError(f"Cannot serialize node of type {type(expression).__name__}")
