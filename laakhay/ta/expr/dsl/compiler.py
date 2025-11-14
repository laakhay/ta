"""Compilation of strategy nodes into laakhay-ta expressions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...api import ta as ta_namespace
from ...api.namespace import ensure_namespace_registered
from ..algebra import Expression
from .nodes import (
    BinaryNode,
    IndicatorNode,
    LiteralNode,
    StrategyError,
    StrategyExpression,
    UnaryNode,
)


class ExpressionCompiler:
    """Compile StrategyExpression nodes into Expression objects."""

    def __init__(self) -> None:
        ensure_namespace_registered()

    def compile(self, expression: StrategyExpression) -> Expression:
        """Compile strategy nodes into a runnable Expression."""
        node = self._compile_node(expression)
        if not isinstance(node, Expression):
            raise StrategyError("Failed to compile expression graph")
        return node

    def _compile_node(self, node: StrategyExpression) -> Expression:
        if isinstance(node, LiteralNode):
            return ta_namespace.literal(float(node.value))

        if isinstance(node, IndicatorNode):
            params = self._compile_params(node.params)
            handle = ta_namespace.indicator(node.name, **params)
            expr = handle._to_expression()
            if node.output:
                raise StrategyError("Indicator output selection is not supported yet")
            return expr

        if isinstance(node, BinaryNode):
            left = self._compile_node(node.left)
            right = self._compile_node(node.right)
            operator = node.operator
            match operator:
                case "add":
                    return left + right
                case "sub":
                    return left - right
                case "mul":
                    return left * right
                case "div":
                    return left / right
                case "mod":
                    return left % right
                case "pow":
                    return left**right
                case "gt":
                    return left > right
                case "gte":
                    return left >= right
                case "lt":
                    return left < right
                case "lte":
                    return left <= right
                case "eq":
                    return left == right
                case "neq":
                    return left != right
                case "and":
                    return left & right
                case "or":
                    return left | right
            raise StrategyError(f"Unsupported binary operator '{operator}'")

        if isinstance(node, UnaryNode):
            operand = self._compile_node(node.operand)
            match node.operator:
                case "not":
                    return ~operand
                case "neg":
                    return -operand
                case "pos":
                    return +operand
            raise StrategyError(f"Unsupported unary operator '{node.operator}'")

        raise StrategyError(f"Unsupported node type '{type(node).__name__}'")

    def _compile_params(self, params: Mapping[str, Any]) -> dict[str, Any]:
        compiled: dict[str, Any] = {}
        for key, value in params.items():
            compiled[key] = self._compile_param_value(value)
        return compiled

    def _compile_param_value(self, value: Any) -> Any:
        from .nodes import BinaryNode as BNode
        from .nodes import IndicatorNode as INode
        from .nodes import LiteralNode as LNode
        from .nodes import UnaryNode as UNode

        if isinstance(value, LNode | INode | BNode | UNode):
            return self._compile_node(value)._node
        return value
