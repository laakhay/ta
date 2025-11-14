"""Indicator extraction and lookback analysis for strategy expressions."""

from __future__ import annotations

from typing import Any

from ...registry.registry import get_global_registry
from .nodes import BinaryNode, IndicatorNode, StrategyExpression, UnaryNode


class IndicatorAnalyzer:
    """Collect indicators from expressions and compute lookback requirements."""

    def __init__(self) -> None:
        self._registry = get_global_registry()

    def collect(self, expression: StrategyExpression) -> list[IndicatorNode]:
        nodes: list[IndicatorNode] = []
        self._collect(expression, nodes)
        return nodes

    def _collect(self, node: StrategyExpression, acc: list[IndicatorNode]) -> None:
        if isinstance(node, IndicatorNode):
            acc.append(node)
        elif isinstance(node, BinaryNode):
            self._collect(node.left, acc)
            self._collect(node.right, acc)
        elif isinstance(node, UnaryNode):
            self._collect(node.operand, acc)

    def compute_trim(self, indicators: list[IndicatorNode]) -> int:
        max_trim = 0
        for indicator in indicators:
            if indicator.name == "select":
                continue
            lookback = self._indicator_lookback(indicator)
            max_trim = max(max_trim, lookback)
        return max_trim

    def _indicator_lookback(self, indicator: IndicatorNode) -> int:
        handle = self._registry.get(indicator.name)
        if handle is None:
            return 0
        metadata = handle.schema.metadata
        lookback = metadata.default_lookback or 0
        for param_name in metadata.lookback_params:
            value = indicator.params.get(param_name)
            if isinstance(value, int | float) and value > 0:
                lookback = max(lookback, int(value))
        if lookback == 0:
            lookback = self._infer_from_params(indicator.params)
        return lookback

    def _infer_from_params(self, params: dict[str, Any]) -> int:
        for _key, value in params.items():
            if isinstance(value, int | float) and value > 0:
                return int(value)
        return 0
