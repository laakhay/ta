"""Parser that converts expression text into strategy nodes."""

from __future__ import annotations

import ast
from typing import Any

from .. import indicators as _indicators  # noqa: F401
from ..api.namespace import ensure_namespace_registered
from ..registry.registry import get_global_registry
from .nodes import (
    BinaryNode,
    IndicatorNode,
    LiteralNode,
    StrategyError,
    StrategyExpression,
    UnaryNode,
)

_BIN_OP_MAP = {
    ast.Add: "add",
    ast.Sub: "sub",
    ast.Mult: "mul",
    ast.Div: "div",
    ast.Mod: "mod",
    ast.Pow: "pow",
}

_COMPARE_MAP = {
    ast.Gt: "gt",
    ast.GtE: "gte",
    ast.Lt: "lt",
    ast.LtE: "lte",
    ast.Eq: "eq",
    ast.NotEq: "neq",
}

_UNARY_MAP = {
    ast.Not: "not",
    ast.UAdd: "pos",
    ast.USub: "neg",
}


class ExpressionParser:
    """Parse Python-esque boolean expressions into strategy nodes."""

    def __init__(self) -> None:
        ensure_namespace_registered()
        # Ensure indicators are loaded before accessing registry
        from .. import indicators  # noqa: F401

        self._registry = get_global_registry()

    def parse_text(self, expression_text: str) -> StrategyExpression:
        expression_text = expression_text.strip()
        if not expression_text:
            raise StrategyError("Expression text cannot be empty")
        try:
            node = ast.parse(expression_text, mode="eval")
        except SyntaxError as exc:  # pragma: no cover - python parser detail
            raise StrategyError(f"Invalid expression: {exc.msg}") from exc
        return self._convert_node(node.body)

    # Node conversions -------------------------------------------------
    def _convert_node(self, node: ast.AST) -> StrategyExpression:
        if isinstance(node, ast.BoolOp):
            return self._convert_bool_op(node)
        if isinstance(node, ast.BinOp):
            return self._convert_bin_op(node)
        if isinstance(node, ast.Compare):
            return self._convert_compare(node)
        if isinstance(node, ast.UnaryOp):
            return self._convert_unary_op(node)
        if isinstance(node, ast.Call):
            return self._convert_indicator_call(node)
        if isinstance(node, ast.Constant):
            return self._convert_constant(node)
        if isinstance(node, ast.Name):
            return self._convert_name(node)
        raise StrategyError(f"Unsupported expression element '{ast.dump(node)}'")

    def _convert_bool_op(self, node: ast.BoolOp) -> StrategyExpression:
        operator = "and" if isinstance(node.op, ast.And) else "or"
        if len(node.values) < 2:
            raise StrategyError("Boolean operations require at least two operands")
        expr = self._convert_node(node.values[0])
        for value in node.values[1:]:
            expr = BinaryNode(operator=operator, left=expr, right=self._convert_node(value))
        return expr

    def _convert_bin_op(self, node: ast.BinOp) -> StrategyExpression:
        operator = _BIN_OP_MAP.get(type(node.op))
        if not operator:
            raise StrategyError(f"Unsupported operator '{ast.dump(node.op)}'")
        return BinaryNode(
            operator=operator,
            left=self._convert_node(node.left),
            right=self._convert_node(node.right),
        )

    def _convert_compare(self, node: ast.Compare) -> StrategyExpression:
        if len(node.ops) != len(node.comparators):
            raise StrategyError("Malformed comparison expression")
        left = self._convert_node(node.left)
        result: StrategyExpression | None = None
        for op, comparator in zip(node.ops, node.comparators, strict=False):
            operator = _COMPARE_MAP.get(type(op))
            if not operator:
                raise StrategyError(f"Unsupported comparison operator '{ast.dump(op)}'")
            right = self._convert_node(comparator)
            comparison = BinaryNode(operator=operator, left=left, right=right)
            result = comparison if result is None else BinaryNode(operator="and", left=result, right=comparison)
            left = right
        assert result is not None
        return result

    def _convert_unary_op(self, node: ast.UnaryOp) -> StrategyExpression:
        operator = _UNARY_MAP.get(type(node.op))
        if not operator:
            raise StrategyError(f"Unsupported unary operator '{ast.dump(node.op)}'")
        return UnaryNode(operator=operator, operand=self._convert_node(node.operand))

    def _convert_indicator_call(self, node: ast.Call) -> StrategyExpression:
        if not isinstance(node.func, ast.Name):
            raise StrategyError("Only simple indicator function calls are allowed")
        name = node.func.id.lower()

        if name == "select":
            return self._convert_select_call(node)

        # Ensure indicators are loaded (in case registry was cleared)
        from .. import indicators  # noqa: F401

        descriptor = self._registry.get(name)
        if descriptor is None:
            raise StrategyError(f"Indicator '{name}' not found")

        param_defs = [
            param for param in descriptor.schema.parameters.values() if param.name.lower() not in {"ctx", "context"}
        ]
        params: dict[str, Any] = {}

        supports_nested = name in {
            "crossup",
            "crossdown",
            "cross",
            "rising",
            "falling",
            "rising_pct",
            "falling_pct",
            "in",
            "in_channel",
            "out",
            "enter",
            "exit",
        }

        if len(node.args) > len(param_defs):
            raise StrategyError(f"Indicator '{name}' accepts at most {len(param_defs)} positional arguments")

        for index, arg in enumerate(node.args):
            param_name = param_defs[index].name
            params[param_name] = self._literal_or_expression(arg, supports_nested, name, param_name)

        for keyword in node.keywords:
            if keyword.arg is None:
                raise StrategyError("Keyword arguments must specify parameter names")
            if keyword.arg.lower() in {"ctx", "context"}:
                raise StrategyError("Context argument is managed automatically and cannot be overridden")
            params[keyword.arg] = self._literal_or_expression(keyword.value, supports_nested, name, keyword.arg)

        return IndicatorNode(name=name, params=params)

    def _convert_select_call(self, node: ast.Call) -> IndicatorNode:
        params: dict[str, Any] = {}
        if len(node.args) > 1:
            raise StrategyError("select() expects at most one positional argument")
        if len(node.args) == 1:
            field_value = self._literal_value(node.args[0])
            if not isinstance(field_value, str):
                raise StrategyError("select() field parameter must be a string literal")
            params["field"] = field_value.lower()
        for keyword in node.keywords:
            if keyword.arg is None:
                raise StrategyError("Keyword arguments must specify parameter names")
            params[keyword.arg] = self._literal_value(keyword.value)
        return IndicatorNode(name="select", params=params)

    def _convert_constant(self, node: ast.Constant) -> LiteralNode:
        value = node.value
        if isinstance(value, bool):
            return LiteralNode(value=1.0 if value else 0.0)
        if isinstance(value, int | float):
            return LiteralNode(value=float(value))
        raise StrategyError(f"Unsupported literal value '{value}'")

    def _convert_name(self, node: ast.Name) -> StrategyExpression:
        lowered = node.id.lower()
        if lowered in {"true", "false"}:
            return LiteralNode(value=1.0 if lowered == "true" else 0.0)
        valid_fields = {
            "close",
            "high",
            "low",
            "open",
            "volume",
            "hlc3",
            "ohlc4",
            "hl2",
            "typical_price",
            "weighted_close",
            "median_price",
            "range",
            "upper_wick",
            "lower_wick",
        }
        if lowered in valid_fields:
            return IndicatorNode(name="select", params={"field": lowered})
        raise StrategyError(f"Unknown identifier '{node.id}'")

    # Helpers -----------------------------------------------------------
    def _literal_value(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, int | float | str | bool):
                return value
            raise StrategyError(f"Unsupported literal type '{type(value).__name__}'")

        if (
            isinstance(node, ast.UnaryOp)
            and isinstance(node.op, ast.USub | ast.UAdd)
            and isinstance(node.operand, ast.Constant)
        ):
            value = node.operand.value
            if not isinstance(value, int | float):
                raise StrategyError("Only numeric literals can be negated")
            return -value if isinstance(node.op, ast.USub) else value

        raise StrategyError("Only literal values are allowed inside indicator parameters")

    def _literal_or_expression(self, node: ast.AST, allow_expression: bool, indicator: str, param: str) -> Any:
        try:
            return self._literal_value(node)
        except StrategyError:
            if allow_expression:
                return self._convert_node(node)
            raise StrategyError(
                f"Indicator '{indicator}' parameter '{param}' must be a literal value; nested expressions are not supported"
            ) from None
