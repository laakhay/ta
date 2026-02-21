"""Indicator emission helpers for preview metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from ...core import Series
from ...registry.registry import get_global_registry
from ..ir.nodes import BinaryOpNode, CallNode, ExprNode, LiteralNode, SourceRefNode, UnaryOpNode

_OSCILLATOR_INDICATORS = {
    "rsi",
    "macd",
    "stochastic",
    "williams",
    "cci",
    "atr",
    "adx",
    "mfi",
    "roc",
    "momentum",
    "stoch",
    "stochrsi",
    "ultosc",
    "ao",
    "ad",
    "cmf",
}


@dataclass(frozen=True)
class IndicatorInputBinding:
    """Resolved dominant input binding for indicator rendering decisions."""

    source: str = "ohlcv"
    field: str = "close"
    symbol: str | None = None
    timeframe: str | None = None
    exchange: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "field": self.field,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "exchange": self.exchange,
        }


@dataclass(frozen=True)
class IndicatorRenderHints:
    """Rendering hints for chart clients."""

    role: str = "line"
    pane_hint: str = "price_overlay"
    style_hint: str = "line"

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "pane_hint": self.pane_hint,
            "style_hint": self.style_hint,
        }


@dataclass(frozen=True)
class IndicatorEmission:
    """Emission payload for one indicator output series."""

    key: str
    node_id: int
    indicator: str
    output: str
    params: dict[str, Any] = field(default_factory=dict)
    input_expr: dict[str, Any] | None = None
    input_binding: IndicatorInputBinding = field(default_factory=IndicatorInputBinding)
    render: IndicatorRenderHints = field(default_factory=IndicatorRenderHints)
    series: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "node_id": self.node_id,
            "indicator": self.indicator,
            "output": self.output,
            "params": self.params,
            "input_expr": self.input_expr,
            "input_binding": self.input_binding.to_dict(),
            "render": self.render.to_dict(),
            "series": self.series,
        }


def build_indicator_emissions(
    *,
    graph_nodes: dict[int, Any],
    node_outputs: dict[int, Any],
) -> list[IndicatorEmission]:
    """Build indicator emissions from planned graph nodes and evaluated outputs."""
    emissions: list[IndicatorEmission] = []
    registry = get_global_registry()

    for node_id, node_data in graph_nodes.items():
        node = node_data.node
        if not _is_indicator_node(node):
            continue
        if node_id not in node_outputs:
            continue

        indicator_name = str(getattr(node, "name", ""))
        raw_params = dict(getattr(node, "kwargs", {}) or {})
        input_node = getattr(node, "args", [])
        input_node = input_node[0] if input_node else None
        binding = _resolve_input_binding(indicator_name, raw_params, input_node)
        outputs = _normalize_outputs(
            value=node_outputs[node_id],
            indicator_name=indicator_name,
            output_metadata=(
                registry.get(indicator_name).schema.output_metadata if registry.get(indicator_name) else {}
            ),
        )
        input_expr = _serialize_expression_node(input_node) if input_node is not None else None

        for output_name, output_series in outputs:
            render = _build_render_hints(
                indicator_name=indicator_name,
                output_name=output_name,
                output_metadata=(
                    registry.get(indicator_name).schema.output_metadata if registry.get(indicator_name) else {}
                ),
                binding=binding,
            )
            emissions.append(
                IndicatorEmission(
                    key=f"i{node_id}" if output_name == "result" else f"i{node_id}_{output_name}",
                    node_id=node_id,
                    indicator=indicator_name,
                    output=output_name,
                    params=raw_params,
                    input_expr=input_expr,
                    input_binding=binding,
                    render=render,
                    series=_series_to_points(output_series),
                )
            )

    emissions.sort(key=lambda item: (item.node_id, item.output))
    return emissions


def _is_indicator_node(node: Any) -> bool:
    return isinstance(node, CallNode)


def _normalize_outputs(
    *,
    value: Any,
    indicator_name: str,
    output_metadata: dict[str, dict[str, Any]],
) -> list[tuple[str, Series[Any]]]:
    if isinstance(value, Series):
        return [("result", value)]

    if isinstance(value, dict):
        items: list[tuple[str, Series[Any]]] = []
        for name, maybe_series in value.items():
            if isinstance(maybe_series, Series):
                items.append((str(name), maybe_series))
        if items:
            return items

    if isinstance(value, tuple):
        names = tuple(output_metadata.keys()) if output_metadata else ()
        items = []
        for index, maybe_series in enumerate(value):
            if not isinstance(maybe_series, Series):
                continue
            name = names[index] if index < len(names) else f"output_{index + 1}"
            items.append((name, maybe_series))
        if items:
            return items

    return []


def _build_render_hints(
    *,
    indicator_name: str,
    output_name: str,
    output_metadata: dict[str, dict[str, Any]],
    binding: IndicatorInputBinding,
) -> IndicatorRenderHints:
    metadata = output_metadata.get(output_name, {}) if output_metadata else {}
    role = str(metadata.get("role", "line"))
    style_hint = "histogram" if role == "histogram" else "line"

    if indicator_name.lower() in _OSCILLATOR_INDICATORS:
        pane_hint = "pane"
    elif binding.field.lower() == "volume":
        pane_hint = "volume"
    elif binding.field.lower() == "mixed":
        pane_hint = "pane"
    else:
        pane_hint = "price_overlay"

    return IndicatorRenderHints(role=role, pane_hint=pane_hint, style_hint=style_hint)


def _resolve_input_binding(
    indicator_name: str,
    params: dict[str, Any],
    input_node: ExprNode | None,
) -> IndicatorInputBinding:
    if input_node is not None:
        resolved = _resolve_binding_from_expression(input_node)
        if resolved is not None:
            return resolved

    source_param = params.get("source")
    if isinstance(source_param, LiteralNode) and isinstance(source_param.value, str):
        source_param = source_param.value
    if isinstance(source_param, str):
        src = source_param.lower()
        if src in {"open", "high", "low", "close", "volume", "price"}:
            return IndicatorInputBinding(source="ohlcv", field=("close" if src == "price" else src))
        return IndicatorInputBinding(source="ohlcv", field=src)

    field_param = params.get("field")
    if isinstance(field_param, LiteralNode) and isinstance(field_param.value, str):
        field_param = field_param.value
    if isinstance(field_param, str):
        field = field_param.lower()
        return IndicatorInputBinding(source="ohlcv", field=("close" if field == "price" else field))

    # Also handle the cases where field is passed positionally via args
    # But those are passed via input_node, which we already resolved above
    # So if we reach here and input_node was a LiteralNode with a string, it might be the field
    if isinstance(input_node, LiteralNode) and isinstance(input_node.value, str):
        val = input_node.value.lower()
        if val in {"open", "high", "low", "close", "volume", "price"}:
            return IndicatorInputBinding(source="ohlcv", field=("close" if val == "price" else val))
        return IndicatorInputBinding(source="ohlcv", field=val)

    handle = get_global_registry().get(indicator_name)
    if handle is not None:
        metadata = handle.schema.metadata
        if metadata.input_field:
            field = metadata.input_field.lower()
            return IndicatorInputBinding(source="ohlcv", field=("close" if field == "price" else field))
        if metadata.required_fields:
            field = str(metadata.required_fields[0]).lower()
            return IndicatorInputBinding(source="ohlcv", field=("close" if field == "price" else field))

    return IndicatorInputBinding(source="ohlcv", field="close")


def _resolve_binding_from_expression(node: ExprNode) -> IndicatorInputBinding | None:
    if isinstance(node, SourceRefNode):
        field = node.field.lower()
        if field in {"open", "high", "low", "close", "volume", "price"}:
            field = "close" if field == "price" else field
        return IndicatorInputBinding(
            source=node.source.lower(),
            field=field,
            symbol=node.symbol,
            timeframe=node.timeframe,
            exchange=node.exchange,
        )

    if isinstance(node, LiteralNode):
        if isinstance(node.value, Series):
            return IndicatorInputBinding(source="series", field="literal")
        return None

    if isinstance(node, UnaryOpNode):
        return _resolve_binding_from_expression(node.operand)

    if isinstance(node, BinaryOpNode):
        left = _resolve_binding_from_expression(node.left)
        right = _resolve_binding_from_expression(node.right)
        if left is None and right is None:
            return None
        if left is None:
            return right
        if right is None:
            return left
        if left.source == right.source and left.field == right.field:
            return left
        return IndicatorInputBinding(source="mixed", field="mixed")

    if _is_indicator_node(node):
        params = dict(getattr(node, "kwargs", {}) or {})

        # If the indicator is the 'select' function, its field argument directly defines the binding
        indicator_name = str(getattr(node, "name", ""))
        if indicator_name == "select":
            field_name = params.get("field")
            if isinstance(field_name, LiteralNode) and isinstance(field_name.value, str):
                field_name = field_name.value
            if isinstance(field_name, str):
                return IndicatorInputBinding(source="ohlcv", field=("close" if field_name == "price" else field_name))

        input_series = getattr(node, "args", [])
        input_series = input_series[0] if input_series else None
        if input_series is not None:
            nested = _resolve_binding_from_expression(input_series)
            if nested is not None:
                return nested
        field_param = params.get("field")
        if isinstance(field_param, str):
            field = field_param.lower()
            return IndicatorInputBinding(source="ohlcv", field=("close" if field == "price" else field))

        source_param = params.get("source")
        if isinstance(source_param, str):
            src = source_param.lower()
            if src in {"open", "high", "low", "close", "volume", "price"}:
                return IndicatorInputBinding(source="ohlcv", field=("close" if src == "price" else src))
            return IndicatorInputBinding(source="ohlcv", field=src)

    return None


def _serialize_expression_node(node: ExprNode | None) -> dict[str, Any] | None:
    """Serialize expression node to something client chart can digest for inputs."""
    if node is None:
        return None
    if isinstance(node, SourceRefNode):
        payload: dict[str, Any] = {
            "type": "source",
            "source": node.source,
            "field": node.field,
            "symbol": node.symbol,
        }
        if node.exchange:
            payload["exchange"] = node.exchange
        if node.timeframe:
            payload["timeframe"] = node.timeframe
        if node.base:
            payload["base"] = node.base
        if node.quote:
            payload["quote"] = node.quote
        if node.instrument_type:
            payload["instrument_type"] = node.instrument_type
        return payload
    if isinstance(node, LiteralNode):
        value = node.value
        if isinstance(value, Series):
            return {"type": "literal_series", "symbol": value.symbol, "timeframe": value.timeframe}
        return {"type": "literal", "value": _json_value(value)}
    if isinstance(node, BinaryOpNode):
        return {
            "type": "binary",
            "operator": node.operator,
            "left": _serialize_expression_node(node.left),
            "right": _serialize_expression_node(node.right),
        }
    if isinstance(node, UnaryOpNode):
        return {
            "type": "unary",
            "operator": node.operator,
            "operand": _serialize_expression_node(node.operand),
        }
    if _is_indicator_node(node):
        nested_input = getattr(node, "args", [])
        nested_input = nested_input[0] if nested_input else None
        return {
            "type": "indicator",
            "name": str(getattr(node, "name", "")),
            "params": dict(getattr(node, "kwargs", {}) or {}),
            "input_expr": _serialize_expression_node(nested_input) if nested_input is not None else None,
        }
    return {"type": "unknown", "repr": repr(node)}


def _series_to_points(series: Series[Any]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for timestamp, value in zip(series.timestamps, series.values, strict=False):
        ts_value = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
        points.append({"timestamp": ts_value, "value": _json_value(value)})
    return points


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float | str) or value is None:
        return value
    return str(value)
