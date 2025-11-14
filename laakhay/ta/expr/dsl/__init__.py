"""High-level helpers for working with strategy expressions."""

from __future__ import annotations

from typing import Any

# Ensure indicators are loaded before creating parser
from ... import indicators  # noqa: F401
from ..algebra import Expression
from .analyzer import IndicatorAnalyzer
from .compiler import ExpressionCompiler
from .nodes import (
    IndicatorNode,
    StrategyError,
    StrategyExpression,
    expression_from_dict,
    expression_to_dict,
)
from .parser import ExpressionParser

__all__ = [
    "StrategyExpression",
    "IndicatorNode",
    "StrategyError",
    "parse_expression_text",
    "expression_from_dict",
    "expression_to_dict",
    "compile_expression",
    "extract_indicator_nodes",
    "compute_trim",
]

_parser = ExpressionParser()
_compiler = ExpressionCompiler()
_analyzer = IndicatorAnalyzer()


def _ensure_expression(expression: StrategyExpression | str | dict[str, Any]) -> StrategyExpression:
    if isinstance(expression, str):
        return _parser.parse_text(expression)
    if isinstance(expression, dict):
        return expression_from_dict(expression)
    return expression


def parse_expression_text(expression_text: str) -> StrategyExpression:
    return _parser.parse_text(expression_text)


def compile_expression(expression: StrategyExpression | str | dict[str, Any]) -> Expression:
    expr = _ensure_expression(expression)
    return _compiler.compile(expr)


def extract_indicator_nodes(expression: StrategyExpression | str | dict[str, Any]) -> list[IndicatorNode]:
    expr = _ensure_expression(expression)
    return _analyzer.collect(expr)


def compute_trim(expression_or_indicators: StrategyExpression | list[IndicatorNode] | str | dict[str, Any]) -> int:
    if isinstance(expression_or_indicators, list):
        return _analyzer.compute_trim(expression_or_indicators)
    expr = _ensure_expression(expression_or_indicators)
    indicators = _analyzer.collect(expr)
    return _analyzer.compute_trim(indicators)
