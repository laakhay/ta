"""Compilation of strategy nodes into laakhay-ta expressions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...api import ta as ta_namespace
from ...api.namespace import ensure_namespace_registered
from ..algebra import Expression
from ..algebra.models import (
    AggregateExpression,
    FilterExpression,
    SourceExpression,
    TimeShiftExpression,
)
from .nodes import (
    AggregateNode,
    AttributeNode,
    BinaryNode,
    FilterNode,
    IndicatorNode,
    LiteralNode,
    StrategyError,
    StrategyExpression,
    TimeShiftNode,
    UnaryNode,
)


class ExpressionCompiler:
    """Compile StrategyExpression nodes into Expression objects."""

    def __init__(
        self,
        default_symbol: str | None = None,
        default_timeframe: str | None = None,
        default_exchange: str | None = None,
    ) -> None:
        ensure_namespace_registered()
        self.default_symbol = default_symbol
        self.default_timeframe = default_timeframe
        self.default_exchange = default_exchange

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

            # If input_expr is present, compile it and pass as input_series parameter
            if node.input_expr is not None:
                input_expr_compiled = self._compile_node(node.input_expr)
                # Pass the compiled expression node as input_series
                # The evaluator will resolve this to a Series at runtime
                params["input_series"] = input_expr_compiled._node

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

        if isinstance(node, AttributeNode):
            return self._compile_attribute_node(node)

        if isinstance(node, FilterNode):
            return self._compile_filter_node(node)

        if isinstance(node, AggregateNode):
            return self._compile_aggregate_node(node)

        if isinstance(node, TimeShiftNode):
            return self._compile_time_shift_node(node)

        raise StrategyError(f"Unsupported node type '{type(node).__name__}'")

    def _compile_params(self, params: Mapping[str, Any]) -> dict[str, Any]:
        compiled: dict[str, Any] = {}
        for key, value in params.items():
            compiled[key] = self._compile_param_value(value)
        return compiled

    def _compile_attribute_node(self, node: AttributeNode) -> Expression:
        """Compile attribute access to SourceExpression."""
        # Use defaults if not specified
        symbol = node.symbol or self.default_symbol
        if not symbol:
            raise StrategyError(
                "Symbol is required for attribute access (provide default_symbol or specify in expression)"
            )

        timeframe = node.timeframe or self.default_timeframe
        exchange = node.exchange or self.default_exchange

        source_expr = SourceExpression(
            symbol=symbol,
            field=node.field,
            exchange=exchange,
            timeframe=timeframe,
            source=node.source,
            base=node.base,
            quote=node.quote,
            instrument_type=node.instrument_type,
        )
        return Expression(source_expr)

    def _compile_filter_node(self, node: FilterNode) -> Expression:
        """Compile filter operation to FilterExpression."""
        series_expr = self._compile_node(node.series)
        condition_expr = self._compile_node(node.condition)

        filter_expr = FilterExpression(series=series_expr._node, condition=condition_expr._node)
        return Expression(filter_expr)

    def _compile_aggregate_node(self, node: AggregateNode) -> Expression:
        """Compile aggregation operation to AggregateExpression."""
        series_expr = self._compile_node(node.series)

        aggregate_expr = AggregateExpression(
            series=series_expr._node,
            operation=node.operation,
            field=node.field,
        )
        return Expression(aggregate_expr)

    def _compile_time_shift_node(self, node: TimeShiftNode) -> Expression:
        """Compile time-based query to TimeShiftExpression."""
        series_expr = self._compile_node(node.series)

        time_shift_expr = TimeShiftExpression(
            series=series_expr._node,
            shift=node.shift,
            operation=node.operation,
        )
        return Expression(time_shift_expr)

    def _compile_param_value(self, value: Any) -> Any:
        from .nodes import AggregateNode as ANode
        from .nodes import AttributeNode as AttrNode
        from .nodes import BinaryNode as BNode
        from .nodes import FilterNode as FNode
        from .nodes import IndicatorNode as INode
        from .nodes import LiteralNode as LNode
        from .nodes import TimeShiftNode as TNode
        from .nodes import UnaryNode as UNode

        if isinstance(value, LNode | INode | BNode | UNode | AttrNode | FNode | ANode | TNode):
            return self._compile_node(value)._node
        return value
