"""Indicator extraction and lookback analysis for strategy expressions."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ...catalog.rust_catalog import get_rust_indicator_meta
from ..ir.nodes import (
    AggregateNode,
    BinaryOpNode,
    CallNode,
    CanonicalExpression,
    FilterNode,
    IndexNode,
    MemberAccessNode,
    TimeShiftNode,
    UnaryOpNode,
)


class IndicatorAnalyzer:
    """Collect indicators from expressions and compute lookback requirements."""

    def __init__(self) -> None:
        pass

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
        meta = _indicator_meta(indicator.name)
        semantics = meta.get("semantics", {}) or {}
        default_lookback = semantics.get("default_lookback")
        lookback = int(default_lookback) if isinstance(default_lookback, int | float) else 0
        for param_name in semantics.get("lookback_params", ()):
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


@lru_cache(maxsize=512)
def _indicator_meta(indicator_name: str) -> dict[str, Any]:
    try:
        return get_rust_indicator_meta(indicator_name)
    except Exception:
        return {}

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
