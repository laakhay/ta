"""Strategy expression node models used for parsing/analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Union, cast


class StrategyError(ValueError):
    """Base error for strategy parsing/compilation."""


@dataclass(slots=True)
class LiteralNode:
    value: float


@dataclass(slots=True)
class IndicatorNode:
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    output: str | None = None
    input_expr: StrategyExpression | None = None  # Optional input expression (e.g., BTC.price, trades.volume)


BinaryOperator = Literal[
    "add",
    "sub",
    "mul",
    "div",
    "mod",
    "pow",
    "gt",
    "gte",
    "lt",
    "lte",
    "eq",
    "neq",
    "and",
    "or",
]


@dataclass(slots=True)
class BinaryNode:
    operator: BinaryOperator
    left: StrategyExpression
    right: StrategyExpression


UnaryOperator = Literal["not", "neg", "pos"]


@dataclass(slots=True)
class UnaryNode:
    operator: UnaryOperator
    operand: StrategyExpression


@dataclass(slots=True)
class AttributeNode:
    """Attribute access: BTC.trades.volume, binance.BTC.price, BTC/USDT.price, BTC/USDT.perp.price"""

    symbol: str  # BTC, ETH, BTC/USDT, etc. (kept for backward compatibility)
    field: str  # price, volume, count, imbalance, etc.
    exchange: str | None = None  # binance, bybit, etc.
    timeframe: str | None = None  # 1h, 15m, etc.
    source: str = "ohlcv"  # ohlcv, trades, orderbook, liquidation
    base: str | None = None  # BTC (from BTC/USDT)
    quote: str | None = None  # USDT (from BTC/USDT)
    instrument_type: str | None = None  # spot, perp, perpetual, futures, future, option


@dataclass(slots=True)
class FilterNode:
    """Filter operation: trades.filter(amount > 1000000)"""

    series: StrategyExpression  # The series to filter (e.g., trades)
    condition: StrategyExpression  # The filter condition (e.g., amount > 1000000)


@dataclass(slots=True)
class AggregateNode:
    """Aggregation: trades.count, trades.sum(amount)"""

    series: StrategyExpression  # The series to aggregate
    operation: str  # 'count', 'sum', 'avg', 'max', 'min'
    field: str | None = None  # Field to aggregate (for sum/avg/max/min)


@dataclass(slots=True)
class TimeShiftNode:
    """Time-based query: price.24h_ago, liquidation.24h"""

    series: StrategyExpression  # The base series
    shift: str  # '24h_ago', '1h_ago', '24h', '1h', etc.
    operation: str | None = None  # 'change', 'change_pct', 'spike', etc.


StrategyExpression = Union[
    LiteralNode, IndicatorNode, BinaryNode, UnaryNode, AttributeNode, FilterNode, AggregateNode, TimeShiftNode
]


def expression_from_dict(data: dict[str, Any]) -> StrategyExpression:
    """Recursively convert a dictionary spec to strategy nodes."""
    node_type = data.get("type")
    if node_type == "literal":
        return LiteralNode(value=float(data["value"]))
    if node_type == "indicator":
        params = cast(dict[str, Any], data.get("params") or {})
        input_expr_data = data.get("input_expr")
        input_expr = expression_from_dict(cast(dict[str, Any], input_expr_data)) if input_expr_data else None
        return IndicatorNode(
            name=str(data["name"]).lower(), params=params, output=data.get("output"), input_expr=input_expr
        )
    if node_type == "binary":
        return BinaryNode(
            operator=cast(BinaryOperator, data["operator"]),
            left=expression_from_dict(cast(dict[str, Any], data["left"])),
            right=expression_from_dict(cast(dict[str, Any], data["right"])),
        )
    if node_type == "unary":
        return UnaryNode(
            operator=cast(UnaryOperator, data["operator"]),
            operand=expression_from_dict(cast(dict[str, Any], data["operand"])),
        )
    if node_type == "attribute":
        return AttributeNode(
            symbol=str(data["symbol"]),
            field=str(data["field"]),
            exchange=data.get("exchange"),
            timeframe=data.get("timeframe"),
            source=str(data.get("source", "ohlcv")),
            base=data.get("base"),
            quote=data.get("quote"),
            instrument_type=data.get("instrument_type"),
        )
    if node_type == "filter":
        return FilterNode(
            series=expression_from_dict(cast(dict[str, Any], data["series"])),
            condition=expression_from_dict(cast(dict[str, Any], data["condition"])),
        )
    if node_type == "aggregate":
        return AggregateNode(
            series=expression_from_dict(cast(dict[str, Any], data["series"])),
            operation=str(data["operation"]),
            field=data.get("field"),
        )
    if node_type == "timeshift":
        return TimeShiftNode(
            series=expression_from_dict(cast(dict[str, Any], data["series"])),
            shift=str(data["shift"]),
            operation=data.get("operation"),
        )
    raise StrategyError(f"Unsupported node type '{node_type}'")


def expression_to_dict(expression: StrategyExpression) -> dict[str, Any]:
    """Convert nodes back to a dictionary representation."""
    if isinstance(expression, LiteralNode):
        return {"type": "literal", "value": expression.value}
    if isinstance(expression, IndicatorNode):
        result = {
            "type": "indicator",
            "name": expression.name,
            "params": expression.params,
            "output": expression.output,
        }
        if expression.input_expr is not None:
            result["input_expr"] = expression_to_dict(expression.input_expr)
        return result
    if isinstance(expression, BinaryNode):
        return {
            "type": "binary",
            "operator": expression.operator,
            "left": expression_to_dict(expression.left),
            "right": expression_to_dict(expression.right),
        }
    if isinstance(expression, UnaryNode):
        return {
            "type": "unary",
            "operator": expression.operator,
            "operand": expression_to_dict(expression.operand),
        }
    if isinstance(expression, AttributeNode):
        result = {
            "type": "attribute",
            "symbol": expression.symbol,
            "source": expression.source,
            "field": expression.field,
        }
        if expression.exchange is not None:
            result["exchange"] = expression.exchange
        if expression.timeframe is not None:
            result["timeframe"] = expression.timeframe
        if expression.base is not None:
            result["base"] = expression.base
        if expression.quote is not None:
            result["quote"] = expression.quote
        if expression.instrument_type is not None:
            result["instrument_type"] = expression.instrument_type
        return result
    if isinstance(expression, FilterNode):
        return {
            "type": "filter",
            "series": expression_to_dict(expression.series),
            "condition": expression_to_dict(expression.condition),
        }
    if isinstance(expression, AggregateNode):
        result = {
            "type": "aggregate",
            "series": expression_to_dict(expression.series),
            "operation": expression.operation,
        }
        if expression.field is not None:
            result["field"] = expression.field
        return result
    if isinstance(expression, TimeShiftNode):
        result = {
            "type": "timeshift",
            "series": expression_to_dict(expression.series),
            "shift": expression.shift,
        }
        if expression.operation is not None:
            result["operation"] = expression.operation
        return result
    raise StrategyError(f"Cannot serialize node of type {type(expression).__name__}")
