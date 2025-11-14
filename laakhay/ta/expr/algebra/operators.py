"""Operator overloading for Series to enable expression building."""

from __future__ import annotations

from typing import Any

from ...core import Series
from ..planner.planner import plan_expression
from ..planner.types import PlanResult, SignalRequirements
from .models import BinaryOp, ExpressionNode, Literal, OperatorType, UnaryOp


class Expression:
    """Expression wrapper that enables operator overloading for Series objects."""

    def __init__(self, node: ExpressionNode):
        self._node = node
        self._plan_cache: PlanResult | None = None

    # ------------------------------------------------------------------
    # Arithmetic / logical operators
    # ------------------------------------------------------------------

    def __add__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.ADD, self._node, other_node))

    def __sub__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.SUB, self._node, other_node))

    def __mul__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MUL, self._node, other_node))

    def __truediv__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.DIV, self._node, other_node))

    def __mod__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MOD, self._node, other_node))

    def __pow__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.POW, self._node, other_node))

    def __eq__(self, other: Expression | Series[Any] | float | int) -> Expression:  # type: ignore[override]
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.EQ, self._node, other_node))

    def __ne__(self, other: Expression | Series[Any] | float | int) -> Expression:  # type: ignore[override]
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.NE, self._node, other_node))

    def __lt__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.LT, self._node, other_node))

    def __le__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.LE, self._node, other_node))

    def __gt__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.GT, self._node, other_node))

    def __ge__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.GE, self._node, other_node))

    def __neg__(self) -> Expression:
        return Expression(UnaryOp(OperatorType.NEG, self._node))

    def __pos__(self) -> Expression:
        return Expression(UnaryOp(OperatorType.POS, self._node))

    def __and__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.AND, self._node, other_node))

    def __or__(self, other: Expression | Series[Any] | float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.OR, self._node, other_node))

    def __invert__(self) -> Expression:
        return Expression(UnaryOp(OperatorType.NOT, self._node))

    def __radd__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.ADD, other_node, self._node))

    def __rsub__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.SUB, other_node, self._node))

    def __rmul__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MUL, other_node, self._node))

    def __rtruediv__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.DIV, other_node, self._node))

    def __rmod__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MOD, other_node, self._node))

    def __rpow__(self, other: float | int) -> Expression:
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.POW, other_node, self._node))

    # ------------------------------------------------------------------
    # Evaluation helpers
    # ------------------------------------------------------------------

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:
        return self._node.evaluate(context)

    def run(self, data: Any) -> Any:
        from ..planner.evaluator import Evaluator

        evaluator = Evaluator()
        return evaluator.evaluate(self, data)

    def requirements(self) -> SignalRequirements:
        return self._ensure_plan().requirements

    def dependencies(self) -> list[str]:
        requirements = self.requirements()
        return sorted({field.name for field in requirements.fields if field.name})

    def describe(self) -> str:
        base = self._node.describe()
        plan = self._ensure_plan()
        req = plan.requirements

        lines = [f"expr: {base}"]

        if req.fields:
            lines.append("fields:")
            for field in req.fields:
                timeframe = field.timeframe or "-"
                lines.append(f"  - {field.name} (timeframe={timeframe}, lookback={field.min_lookback})")

        if req.derived:
            lines.append("derived:")
            for derived in req.derived:
                params = ", ".join(f"{key}={value}" for key, value in derived.params) if derived.params else ""
                suffix = f"({params})" if params else ""
                lines.append(f"  - {derived.name}{suffix}")

        alignment = plan.alignment
        lines.append(
            "alignment: "
            f"how={alignment.how}, fill={alignment.fill}, "
            f"left_fill={alignment.left_fill_value}, right_fill={alignment.right_fill_value}"
        )

        return "\n".join(lines)

    def to_dot(self) -> str:
        plan = self._ensure_plan()
        lines = ["digraph Expression {", "  rankdir=LR;"]
        for node_id, node in plan.graph.nodes.items():
            label = _node_label(node.node)
            lines.append(f'  n{node_id} [shape=box,label="{label}"];\n')
            for child in node.children:
                lines.append(f"  n{node_id} -> n{child};")
        lines.append("}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_plan(self) -> PlanResult:
        if self._plan_cache is None:
            self._plan_cache = plan_expression(self._node)
        return self._plan_cache


def _node_label(node: ExpressionNode) -> str:
    t = type(node).__name__
    if isinstance(node, BinaryOp):
        return f"{t}\\n{node.operator.value}"
    if isinstance(node, UnaryOp):
        return f"{t}\\n{node.operator.value}"
    if isinstance(node, Literal):
        v = node.value
        if hasattr(v, "symbol") and hasattr(v, "timeframe"):
            return f"Literal\\nSeries({getattr(v, 'symbol', '?')} {getattr(v, 'timeframe', '?')})"
        return f"Literal\\n{str(v)[:24]}"
    if node.__class__.__name__ == "IndicatorNode" and hasattr(node, "name"):
        return f"Indicator\\n{node.name}"
    return t


def _to_node(
    value: Expression | ExpressionNode | Series[Any] | float | int,
) -> ExpressionNode:
    if isinstance(value, Expression):
        return value._node  # type: ignore[misc]
    if isinstance(value, ExpressionNode):
        return value
    return Literal(value)


def as_expression(series: Series[Any]) -> Expression:
    return Expression(Literal(series))
