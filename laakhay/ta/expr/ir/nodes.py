"""Canonical IR node definitions for the strategy expression engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Union

from .types import ExprType

SCALAR_SYMBOL = "__SCALAR__"


class ExprNode:
    """Base class for all canonical IR nodes."""

    pass


@dataclass(slots=True, unsafe_hash=True)
class LiteralNode(ExprNode):
    """A literal value (number, bool, string)."""

    value: float | bool | str
    span_start: int | None = None
    span_end: int | None = None
    type_tag: ExprType = "scalar_number"


@dataclass(slots=True, unsafe_hash=True)
class SourceRefNode(ExprNode):
    """Fully resolved source/field identity. Replaces AttributeNode."""

    symbol: str
    field: str
    source: str = "ohlcv"
    exchange: str | None = None
    timeframe: str | None = None
    base: str | None = None
    quote: str | None = None
    instrument_type: str | None = None
    span_start: int | None = None
    span_end: int | None = None
    type_tag: ExprType = "series_number"


@dataclass(slots=True, unsafe_hash=True)
class CallNode(ExprNode):
    """Indicator or function call. Replaces IndicatorNode."""

    name: str
    args: list[CanonicalExpression] = field(default_factory=list)
    kwargs: dict[str, CanonicalExpression] = field(default_factory=dict)
    output: str | None = None
    span_start: int | None = None
    span_end: int | None = None
    type_tag: ExprType = "series_number"

    @property
    def input_expr(self) -> CanonicalExpression | None:
        """Legacy compatibility: first positional argument as explicit input."""
        if not self.args:
            return None
        first = self.args[0]
        return None if isinstance(first, LiteralNode) else first

    @property
    def params(self) -> dict[str, Any]:
        """Legacy compatibility alias for kwargs."""
        out: dict[str, Any] = {}
        for key, value in self.kwargs.items():
            out[key] = value.value if isinstance(value, LiteralNode) else value
        return out


BinaryOperator = Literal["add", "sub", "mul", "div", "mod", "pow", "gt", "gte", "lt", "lte", "eq", "neq", "and", "or"]


@dataclass(slots=True, unsafe_hash=True)
class BinaryOpNode(ExprNode):
    """Binary operation."""

    operator: BinaryOperator
    left: CanonicalExpression
    right: CanonicalExpression
    span_start: int | None = None
    span_end: int | None = None
    type_tag: ExprType = "unknown"


UnaryOperator = Literal["not", "neg", "pos"]


@dataclass(slots=True, unsafe_hash=True)
class UnaryOpNode(ExprNode):
    """Unary operation."""

    operator: UnaryOperator
    operand: CanonicalExpression
    span_start: int | None = None
    span_end: int | None = None
    type_tag: ExprType = "unknown"


@dataclass(slots=True, unsafe_hash=True)
class FilterNode(ExprNode):
    """Filter operation on a series."""

    series: CanonicalExpression
    condition: CanonicalExpression
    span_start: int | None = None
    span_end: int | None = None
    type_tag: ExprType = "series_number"


@dataclass(slots=True, unsafe_hash=True)
class AggregateNode(ExprNode):
    """Aggregation over a series."""

    series: CanonicalExpression
    operation: str
    field: str | None = None
    span_start: int | None = None
    span_end: int | None = None
    type_tag: ExprType = "series_number"


@dataclass(slots=True, unsafe_hash=True)
class TimeShiftNode(ExprNode):
    """Time-shift operation on a series."""

    series: CanonicalExpression
    shift: str
    operation: str | None = None
    span_start: int | None = None
    span_end: int | None = None
    type_tag: ExprType = "series_number"


@dataclass(slots=True, unsafe_hash=True)
class MemberAccessNode(ExprNode):
    """Accessing a property of a struct/record output. (Gated for future)"""

    expr: CanonicalExpression
    member: str
    span_start: int | None = None
    span_end: int | None = None
    type_tag: ExprType = "unknown"


@dataclass(slots=True, unsafe_hash=True)
class IndexNode(ExprNode):
    """Array/list indexing. (Gated for future)"""

    expr: CanonicalExpression
    index: CanonicalExpression
    span_start: int | None = None
    span_end: int | None = None
    type_tag: ExprType = "unknown"


CanonicalExpression = Union[
    LiteralNode,
    SourceRefNode,
    CallNode,
    BinaryOpNode,
    UnaryOpNode,
    FilterNode,
    AggregateNode,
    TimeShiftNode,
    MemberAccessNode,
    IndexNode,
]
