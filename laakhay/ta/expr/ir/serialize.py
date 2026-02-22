"""Serialization and deserialization of the canonical expression IR."""

from typing import Any, cast

from .nodes import (
    AggregateNode,
    BinaryOperator,
    BinaryOpNode,
    CallNode,
    CanonicalExpression,
    FilterNode,
    IndexNode,
    LiteralNode,
    MemberAccessNode,
    SourceRefNode,
    TimeShiftNode,
    UnaryOperator,
    UnaryOpNode,
)
from .types import ExprType


class IRSearializationError(ValueError):
    """Error raised during IR serialization/deserialization."""


def _dump_expr_node(expr: Any, result: dict[str, Any]) -> None:
    if expr.span_start is not None:
        result["span_start"] = expr.span_start
    if expr.span_end is not None:
        result["span_end"] = expr.span_end
    if expr.type_tag and expr.type_tag != "unknown":
        result["type_tag"] = expr.type_tag


def _load_expr_node(data: dict[str, Any], kwargs: dict[str, Any]) -> None:
    if "span_start" in data:
        kwargs["span_start"] = data["span_start"]
    if "span_end" in data:
        kwargs["span_end"] = data["span_end"]
    if "type_tag" in data:
        kwargs["type_tag"] = cast(ExprType, data["type_tag"])


def ir_to_dict(expr: CanonicalExpression) -> dict[str, Any]:
    """Convert canonical IR to dictionary."""
    if isinstance(expr, LiteralNode):
        result = {"type": "literal", "value": expr.value}
        _dump_expr_node(expr, result)
        return result
    if isinstance(expr, SourceRefNode):
        result = {
            "type": "source_ref",
            "symbol": expr.symbol,
            "field": expr.field,
            "source": expr.source,
        }
        if expr.exchange is not None:
            result["exchange"] = expr.exchange
        if expr.timeframe is not None:
            result["timeframe"] = expr.timeframe
        if expr.base is not None:
            result["base"] = expr.base
        if expr.quote is not None:
            result["quote"] = expr.quote
        if expr.instrument_type is not None:
            result["instrument_type"] = expr.instrument_type
        _dump_expr_node(expr, result)
        return result
    if isinstance(expr, CallNode):
        result = {
            "type": "call",
            "name": expr.name,
            "args": [ir_to_dict(arg) for arg in expr.args],
            "kwargs": {k: ir_to_dict(v) for k, v in expr.kwargs.items()},
        }
        if expr.output is not None:
            result["output"] = expr.output
        _dump_expr_node(expr, result)
        return result
    if isinstance(expr, BinaryOpNode):
        result = {
            "type": "binary_op",
            "operator": expr.operator,
            "left": ir_to_dict(expr.left),
            "right": ir_to_dict(expr.right),
        }
        _dump_expr_node(expr, result)
        return result
    if isinstance(expr, UnaryOpNode):
        result = {
            "type": "unary_op",
            "operator": expr.operator,
            "operand": ir_to_dict(expr.operand),
        }
        _dump_expr_node(expr, result)
        return result
    if isinstance(expr, FilterNode):
        result = {
            "type": "filter",
            "series": ir_to_dict(expr.series),
            "condition": ir_to_dict(expr.condition),
        }
        _dump_expr_node(expr, result)
        return result
    if isinstance(expr, AggregateNode):
        result = {
            "type": "aggregate",
            "series": ir_to_dict(expr.series),
            "operation": expr.operation,
        }
        if expr.field is not None:
            result["field"] = expr.field
        _dump_expr_node(expr, result)
        return result
    if isinstance(expr, TimeShiftNode):
        result = {
            "type": "timeshift",
            "series": ir_to_dict(expr.series),
            "shift": expr.shift,
        }
        if expr.operation is not None:
            result["operation"] = expr.operation
        _dump_expr_node(expr, result)
        return result
    if isinstance(expr, MemberAccessNode):
        result = {
            "type": "member_access",
            "expr": ir_to_dict(expr.expr),
            "member": expr.member,
        }
        _dump_expr_node(expr, result)
        return result
    if isinstance(expr, IndexNode):
        result = {
            "type": "index",
            "expr": ir_to_dict(expr.expr),
            "index": ir_to_dict(expr.index),
        }
        _dump_expr_node(expr, result)
        return result
    raise IRSearializationError(f"Cannot serialize node of type {type(expr).__name__}")


def ir_from_dict(data: dict[str, Any]) -> CanonicalExpression:
    """Convert dictionary to canonical IR."""
    node_type = data.get("type")
    kwargs: dict[str, Any] = {}
    _load_expr_node(data, kwargs)

    if node_type == "literal":
        return LiteralNode(value=data["value"], **kwargs)
    if node_type == "source_ref":
        symbol = data.get("symbol")
        field = data.get("field")
        return SourceRefNode(
            symbol=str(symbol) if symbol is not None else None,
            field=str(field) if field is not None else None,
            source=str(data.get("source", "ohlcv")),
            exchange=data.get("exchange"),
            timeframe=data.get("timeframe"),
            base=data.get("base"),
            quote=data.get("quote"),
            instrument_type=data.get("instrument_type"),
            **kwargs,
        )
    if node_type == "call":
        args = [ir_from_dict(cast(dict[str, Any], arg)) for arg in data.get("args", [])]
        kw_args = {k: ir_from_dict(cast(dict[str, Any], v)) for k, v in data.get("kwargs", {}).items()}
        return CallNode(
            name=str(data["name"]).lower(),
            args=args,
            kwargs=kw_args,
            output=data.get("output"),
            **kwargs,
        )
    if node_type == "binary_op":
        return BinaryOpNode(
            operator=cast(BinaryOperator, data["operator"]),
            left=ir_from_dict(cast(dict[str, Any], data["left"])),
            right=ir_from_dict(cast(dict[str, Any], data["right"])),
            **kwargs,
        )
    if node_type == "unary_op":
        return UnaryOpNode(
            operator=cast(UnaryOperator, data["operator"]),
            operand=ir_from_dict(cast(dict[str, Any], data["operand"])),
            **kwargs,
        )
    if node_type == "filter":
        return FilterNode(
            series=ir_from_dict(cast(dict[str, Any], data["series"])),
            condition=ir_from_dict(cast(dict[str, Any], data["condition"])),
            **kwargs,
        )
    if node_type == "aggregate":
        return AggregateNode(
            series=ir_from_dict(cast(dict[str, Any], data["series"])),
            operation=str(data["operation"]),
            field=data.get("field"),
            **kwargs,
        )
    if node_type == "timeshift":
        return TimeShiftNode(
            series=ir_from_dict(cast(dict[str, Any], data["series"])),
            shift=str(data["shift"]),
            operation=data.get("operation"),
            **kwargs,
        )
    if node_type == "member_access":
        return MemberAccessNode(
            expr=ir_from_dict(cast(dict[str, Any], data["expr"])),
            member=str(data["member"]),
            **kwargs,
        )
    if node_type == "index":
        return IndexNode(
            expr=ir_from_dict(cast(dict[str, Any], data["expr"])),
            index=ir_from_dict(cast(dict[str, Any], data["index"])),
            **kwargs,
        )
    raise IRSearializationError(f"Unsupported node type '{node_type}'")
