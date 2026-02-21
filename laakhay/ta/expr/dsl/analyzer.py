"""Indicator extraction and lookback analysis for strategy expressions."""

from __future__ import annotations

from typing import Any

from ...registry.registry import get_global_registry
from ..ir.nodes import (
    CanonicalExpression,
    BinaryOpNode,
    CallNode,
    UnaryOpNode,
    FilterNode,
    AggregateNode,
    TimeShiftNode,
    MemberAccessNode,
    IndexNode
)


class IndicatorAnalyzer:
    """Collect indicators from expressions and compute lookback requirements."""

    def __init__(self) -> None:
        self._registry = get_global_registry()

    def collect(self, expression: CanonicalExpression) -> list[CallNode]:
        nodes: list[CallNode] = []
        self._collect(expression, nodes)
        return nodes

    def _collect(self, node: CanonicalExpression, acc: list[CallNode]) -> None:
        if isinstance(node, CallNode):
            acc.append(node)
            for arg in node.args:
                self._collect(arg, acc)
            for val in node.kwargs.values():
                self._collect(val, acc)
        elif isinstance(node, BinaryOpNode):
            self._collect(node.left, acc)
            self._collect(node.right, acc)
        elif isinstance(node, UnaryOpNode):
            self._collect(node.operand, acc)
        elif isinstance(node, FilterNode):
            self._collect(node.series, acc)
            self._collect(node.condition, acc)
        elif isinstance(node, AggregateNode):
            self._collect(node.series, acc)
        elif isinstance(node, TimeShiftNode):
            self._collect(node.series, acc)
        elif isinstance(node, MemberAccessNode):
            self._collect(node.expr, acc)
        elif isinstance(node, IndexNode):
            self._collect(node.expr, acc)
            self._collect(node.index, acc)

    def compute_trim(self, indicators: list[CallNode]) -> int:
        max_trim = 0
        for indicator in indicators:
            if indicator.name == "select":
                continue
            lookback = self._indicator_lookback(indicator)
            max_trim = max(max_trim, lookback)
        return max_trim

    def _indicator_lookback(self, indicator: CallNode) -> int:
        handle = self._registry.get(indicator.name)
        if handle is None:
            return 0
        metadata = handle.schema.metadata
        lookback = metadata.default_lookback or 0
        for param_name in metadata.lookback_params:
            value = indicator.kwargs.get(param_name)
            # handle cases where the param might be an argument, simplifying here to just check literals
            if getattr(value, "type_tag", None) == "scalar_number":
                num = getattr(value, "value", 0)
                if isinstance(num, int | float) and num > 0:
                    lookback = max(lookback, int(num))
            elif value is None:
                for arg in indicator.args:
                    if getattr(arg, "type_tag", None) == "scalar_number":
                        num = getattr(arg, "value", 0)
                        if isinstance(num, int | float) and num > 0:
                            lookback = max(lookback, int(num))
                            break
        if lookback == 0:
            lookback = self._infer_from_params(indicator.kwargs) or self._infer_from_args(indicator.args)
        return lookback

    def _infer_from_params(self, params: dict[str, Any]) -> int:
        for _key, value in params.items():
            if getattr(value, "type_tag", None) == "scalar_number":
                num = getattr(value, "value", 0)
                if isinstance(num, int | float) and num > 0:
                    return int(num)
        return 0

    def _infer_from_args(self, args: tuple[Any, ...] | list[Any]) -> int:
        for value in args:
            if getattr(value, "type_tag", None) == "scalar_number":
                num = getattr(value, "value", 0)
                if isinstance(num, int | float) and num > 0:
                    return int(num)
        return 0
