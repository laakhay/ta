"""Operator overloading for Series to enable expression building."""

from __future__ import annotations

from typing import Any

from ...core import Series
from ..execution.runner import evaluate_plan
from ..ir.nodes import (
    BinaryOpNode,
    CallNode,
    CanonicalExpression,
    LiteralNode,
    UnaryOpNode,
)
from ..planner.planner import plan_expression
from ..planner.types import PlanResult, SignalRequirements


class Expression:
    """Expression wrapper that enables operator overloading for Series objects."""

    def __init__(self, node: CanonicalExpression):
        self._node = node
        self._plan_cache: PlanResult | None = None

    # ------------------------------------------------------------------
    # Arithmetic / logical operators
    # ------------------------------------------------------------------

    def __add__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("add", self._node, other_node))

    def __sub__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("sub", self._node, other_node))

    def __mul__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("mul", self._node, other_node))

    def __truediv__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("div", self._node, other_node))

    def __mod__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("mod", self._node, other_node))

    def __pow__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("pow", self._node, other_node))

    def __eq__(self, other: Expression | Series[Any] | float | int) -> Expression:  # type: ignore[override]
        other_node = _to_node(other)
        return Expression(BinaryOpNode("eq", self._node, other_node))

    def __ne__(self, other: Expression | Series[Any] | float | int) -> Expression:  # type: ignore[override]
        other_node = _to_node(other)
        return Expression(BinaryOpNode("neq", self._node, other_node))

    def __lt__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("lt", self._node, other_node))

    def __le__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("lte", self._node, other_node))

    def __gt__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("gt", self._node, other_node))

    def __ge__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("gte", self._node, other_node))

    def __neg__(self) -> Expression:
        return Expression(UnaryOpNode("neg", self._node))

    def __pos__(self) -> Expression:
        return Expression(UnaryOpNode("pos", self._node))

    def __and__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("and", self._node, other_node))

    def __or__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("or", self._node, other_node))

    def __invert__(self) -> Expression:
        return Expression(UnaryOpNode("not", self._node))

    def __radd__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("add", other_node, self._node))

    def __rsub__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("sub", other_node, self._node))

    def __rmul__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("mul", other_node, self._node))

    def __rtruediv__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("div", other_node, self._node))

    def __rmod__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("mod", other_node, self._node))

    def __rpow__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOpNode("pow", other_node, self._node))

    # ------------------------------------------------------------------
    # Evaluation helpers
    # ------------------------------------------------------------------

    def evaluate(self, context: dict[str, Series[Any]] | None) -> Series[Any]:
        # Handled by evaluator
        from ..planner.evaluator import Evaluator

        result = Evaluator().evaluate(self, context or {})
        if isinstance(result, Series):
            return result
        from .scalar_helpers import _make_scalar_series

        return _make_scalar_series(result)

    def run(self, data: Any, return_all_outputs: bool = False) -> Any:
        plan = self._ensure_plan()
        return evaluate_plan(plan, data, return_all_outputs=return_all_outputs)

    def requirements(self) -> SignalRequirements:
        return self._ensure_plan().requirements

    def dependencies(self) -> list[str]:
        requirements = self.requirements()
        return sorted({req.field for req in requirements.data_requirements if req.field})

    def describe(self) -> str:
        base = _expr_text(self._node)
        plan = self._ensure_plan()
        req = plan.requirements

        lines = [f"expr: {base}"]

        if req.data_requirements:
            lines.append("data_requirements:")
            for data_req in req.data_requirements:
                timeframe = data_req.timeframe or "-"
                symbol = data_req.symbol or "*"
                exchange = data_req.exchange or "*"
                lines.append(
                    f"  - {data_req.source}.{data_req.field} "
                    f"(symbol={symbol}, exchange={exchange}, timeframe={timeframe}, lookback={data_req.min_lookback})"
                )

        alignment = plan.alignment
        lines.append(
            "alignment: "
            f"how={alignment.how}, fill={alignment.fill}, "
            f"left_fill={alignment.left_fill_value}, right_fill={alignment.right_fill_value}"
        )

        return "\\n".join(lines)

    def to_dot(self) -> str:
        plan = self._ensure_plan()
        lines = ["digraph Expression {", "  rankdir=LR;"]
        for node_id, node in plan.graph.nodes.items():
            label = _node_label(node.node)
            lines.append(f'  n{node_id} [shape=box,label="{label}"];\\n')
            for child in node.children:
                lines.append(f"  n{node_id} -> n{child};")
        lines.append("}")
        return "\\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_plan(self) -> PlanResult:
        if self._plan_cache is None:
            self._plan_cache = plan_expression(self._node)
        return self._plan_cache


def _node_label(node: CanonicalExpression) -> str:
    t = type(node).__name__
    if isinstance(node, BinaryOpNode):
        return f"{t}\\n{node.operator}"
    if isinstance(node, UnaryOpNode):
        return f"{t}\\n{node.operator}"
    if isinstance(node, LiteralNode):
        v = node.value
        if hasattr(v, "symbol") and hasattr(v, "timeframe"):
            return f"LiteralNode\\nSeries({getattr(v, 'symbol', '?')} {getattr(v, 'timeframe', '?')})"
        return f"LiteralNode\\n{str(v)[:24]}"
    if isinstance(node, CallNode):
        params = []
        for key, value in node.kwargs.items():
            if isinstance(value, LiteralNode):
                params.append(f"{key}={value.value}")
        suffix = f"({', '.join(params)})" if params else ""
        return f"CallNode\\n{node.name}{suffix}"
    return t


def _expr_text(node: CanonicalExpression) -> str:
    if isinstance(node, LiteralNode):
        return str(node.value)
    if isinstance(node, BinaryOpNode):
        op_map = {
            "add": "+",
            "sub": "-",
            "mul": "*",
            "div": "/",
            "mod": "%",
            "pow": "**",
            "eq": "==",
            "neq": "!=",
            "lt": "<",
            "lte": "<=",
            "gt": ">",
            "gte": ">=",
            "and": "and",
            "or": "or",
        }
        return f"({_expr_text(node.left)} {op_map.get(node.operator, node.operator)} {_expr_text(node.right)})"
    if isinstance(node, UnaryOpNode):
        op_map = {"neg": "-", "pos": "+", "not": "not "}
        return f"{op_map.get(node.operator, node.operator)}{_expr_text(node.operand)}"
    if isinstance(node, CallNode):
        params = []
        for key, value in node.kwargs.items():
            params.append(f"{key}={_expr_text(value)}")
        args = [_expr_text(arg) for arg in node.args]
        joined = ", ".join(args + params)
        return f"{node.name}({joined})"
    return _node_label(node)


def _to_node(
    value: Expression | CanonicalExpression | Series[Any] | float | int,
) -> CanonicalExpression:
    if isinstance(value, Expression):
        return value._node  # type: ignore[misc]
    if hasattr(value, "_to_expression"):
        try:
            expr = value._to_expression()
            if isinstance(expr, Expression):
                return expr._node  # type: ignore[misc]
        except Exception:
            pass
    if isinstance(value, tuple) and hasattr(value, "span_start"):  # Hack for CanonicalExpression
        return value
    if type(value).__name__ in [
        "LiteralNode",
        "CallNode",
        "BinaryOpNode",
        "UnaryOpNode",
        "FilterNode",
        "AggregateNode",
        "TimeShiftNode",
        "SourceRefNode",
    ]:
        return value
    return LiteralNode(value)


def as_expression(series: Series[Any]) -> Expression:
    if isinstance(series, Expression):
        return series
    return Expression(_to_node(series))


# ------------------------------------------------------------------
# Scalar series helpers (Proxied from scalar_helpers.py)
# ------------------------------------------------------------------
