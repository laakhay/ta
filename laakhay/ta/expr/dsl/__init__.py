"""High-level helpers for working with strategy expressions."""

from __future__ import annotations

from typing import Any

# Ensure indicators are loaded before creating parser
from ... import indicators  # noqa: F401
from ..algebra import Expression
from ..compile import compile_to_ir
from ..ir.nodes import CallNode, CanonicalExpression
from ..ir.serialize import ir_from_dict, ir_to_dict
from .analyzer import IndicatorAnalyzer
from .parser import StrategyError

__all__ = [
    "StrategyError",
    "parse_expression_text",
    "expression_from_dict",
    "expression_to_dict",
    "compile_expression",
    "extract_indicator_nodes",
    "compute_trim",
    "CanonicalExpression",
    "CallNode",
]

_analyzer = IndicatorAnalyzer()


def _ensure_expression(expression: CanonicalExpression | str | dict[str, Any]) -> CanonicalExpression:
    if isinstance(expression, str):
        return compile_to_ir(expression)
    if isinstance(expression, dict):
        return ir_from_dict(expression)
    return expression


def parse_expression_text(expression_text: str) -> CanonicalExpression:
    return compile_to_ir(expression_text)


def expression_from_dict(data: dict[str, Any]) -> CanonicalExpression:
    return ir_from_dict(data)


def expression_to_dict(expr: CanonicalExpression) -> dict[str, Any]:
    return ir_to_dict(expr)


def compile_expression(expression: CanonicalExpression | str | dict[str, Any]) -> Expression:
    expr = _ensure_expression(expression)
    return Expression(expr)


def extract_indicator_nodes(expression: CanonicalExpression | str | dict[str, Any]) -> list[CallNode]:
    expr = _ensure_expression(expression)
    return _analyzer.collect(expr)


def compute_trim(expression_or_indicators: CanonicalExpression | list[CallNode] | str | dict[str, Any]) -> int:
    if isinstance(expression_or_indicators, list):
        return _analyzer.compute_trim(expression_or_indicators)
    expr = _ensure_expression(expression_or_indicators)
    indicators = _analyzer.collect(expr)
    return _analyzer.compute_trim(indicators)
