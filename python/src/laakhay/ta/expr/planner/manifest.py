"""Capability manifest generation for strategies API."""

from __future__ import annotations

import keyword
from typing import Any

from ...registry.registry import get_global_registry
from ..semantics.source_schema import SOURCE_DEFS
from .types import PlanResult


def generate_capability_manifest() -> dict[str, Any]:
    """Generate capability manifest for /api/v1/strategies/capabilities.

    This manifest describes:
    - Available data sources (ohlcv, trades, orderbook, liquidation)
    - Available fields per source
    - Available indicators (categorized)
    - Available operators
    - Expression syntax examples
    - Exchange-specific source support (merged with laakhay-data metadata)

    Returns:
        Dictionary with capability information for frontend/backend consumption.
    """
    from ...catalog import describe_indicator

    registry = get_global_registry()

    # Get all registered indicators including aliases
    indicators = []
    all_names = registry.list_all_names()

    for name in all_names:
        handle = registry.get(name)
        if handle:
            # Determine if this is an alias by comparing name with handle.name
            is_alias = name != handle.name
            if is_alias and keyword.iskeyword(name):
                # Skip aliases that are Python keywords (e.g. "in") because they
                # cannot be called in expression text syntax.
                continue

            # Use CatalogBuilder logic to get rich metadata
            try:
                descriptor = describe_indicator(handle.name)
                category = descriptor.category
                description = descriptor.description
                params = descriptor.get_parameter_specs()
                outputs = [o.name for o in descriptor.outputs]
            except Exception:
                # Fallback: derive from IndicatorSpec (canonical source)
                spec = handle.indicator_spec
                category = "custom"
                description = spec.description or name
                params = {
                    p_name: {
                        "name": p.name,
                        "param_type": p.type.__name__ if p.type else "unknown",
                        "required": p.required,
                        "default_value": p.default,
                    }
                    for p_name, p in spec.params.items()
                    if p_name.lower() not in ("ctx", "context")
                }
                outputs = list(spec.outputs.keys()) if spec.outputs else []

            indicators.append(
                {
                    "name": name,
                    "description": description,
                    "category": category,
                    "is_alias": is_alias,
                    "target": handle.name if is_alias else None,
                    "parameters": {
                        p_name: {
                            "type": p_data.get("param_type") or p_data.get("type", "unknown"),
                            "required": p_data.get("required", False),
                            "default": p_data.get("public_default") or p_data.get("default_value"),
                        }
                        for p_name, p_data in params.items()
                    },
                    "outputs": outputs,
                }
            )

    # Use canonical shared schema for source/field definitions.
    sources = _canonical_sources()

    # Extract operators from parser
    operators = _extract_operators_from_parser()

    # Merge with laakhay-data exchange metadata to filter unsupported combos
    exchange_source_support = _merge_exchange_metadata(sources)

    # Define expression syntax examples
    examples = {
        "basic": [
            "sma(20) > sma(50)",
            "rsi(14) < 30",
            "close > 50000",
        ],
        "multi_source": [
            "ohlcv.close > 50000",
            "trades.volume > 1000000",
            "orderbook.imbalance > 0.5",
        ],
        "filters": [
            "trades.filter(amount > 1000000).count > 10",
        ],
        "aggregations": [
            "trades.sum(amount) > 50000000",
            "trades.count > 100",
        ],
        "time_shifts": [
            "close.24h_ago < close",
            "volume.change_pct_24h > 10",
        ],
    }

    return {
        "sources": sources,
        "exchange_source_support": exchange_source_support,
        "indicators": sorted(indicators, key=lambda x: (x["category"], x["name"])),
        "operators": operators,
        "examples": examples,
        "version": "1.3.0",  # Bumped version for rich metadata
        "dsl_version": "1.0.0",
        "features": {
            "multi_source": False,
            "explicit_indicator_inputs": True,
            "filters": True,
            "aggregations": True,
            "time_shifts": True,
        },
    }


def _canonical_sources() -> dict[str, dict[str, Any]]:
    return {
        src.name: {
            "fields": sorted(src.field_names),
            "description": src.description,
        }
        for src in SOURCE_DEFS.values()
    }


def _extract_operators_from_parser() -> dict[str, list[str]]:
    """Extract operators from parser's operator maps."""
    # Map operator names to their symbols
    operator_symbols = {
        "add": "+",
        "sub": "-",
        "mul": "*",
        "div": "/",
        "mod": "%",
        "pow": "**",
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "eq": "==",
        "neq": "!=",
    }

    # Lazy import to avoid circular dependencies
    from ..dsl import parser as parser_module

    arithmetic_ops = []
    comparison_ops = []
    logical_ops = ["and", "or", "not"]

    # Get binary operators
    if hasattr(parser_module, "_BIN_OP_MAP"):
        for op_name in parser_module._BIN_OP_MAP.values():
            if op_name in operator_symbols:
                symbol = operator_symbols[op_name]
                if op_name in ("add", "sub", "mul", "div", "mod", "pow"):
                    arithmetic_ops.append(symbol)
                elif op_name in ("gt", "gte", "lt", "lte", "eq", "neq"):
                    comparison_ops.append(symbol)

    # Get comparison operators
    if hasattr(parser_module, "_COMPARE_MAP"):
        for op_name in parser_module._COMPARE_MAP.values():
            if op_name in operator_symbols:
                symbol = operator_symbols[op_name]
                if symbol not in comparison_ops:
                    comparison_ops.append(symbol)

    return {
        "arithmetic": sorted(set(arithmetic_ops)),
        "comparison": sorted(set(comparison_ops)),
        "logical": logical_ops,
    }


def _merge_exchange_metadata(sources: dict[str, dict[str, Any]]) -> dict[str, dict[str, dict[str, bool]]]:
    """
    Merge TA source definitions with laakhay-data exchange metadata.

    This filters out unsupported source/exchange combinations (e.g., Coinbase doesn't
    support liquidations since it's spot-only).

    Args:
        sources: Dictionary of source definitions from TA parser

    Returns:
        Dictionary mapping exchange -> source -> support flags
        Example: {"binance": {"ohlcv": {"rest": True, "ws": True}, ...}, ...}
    """
    try:
        from laakhay.data import get_all_capabilities
    except ImportError:
        # If laakhay-data is not available, return empty dict
        return {}

    # Map TA source names to laakhay-data data_type names
    source_to_datatype = {
        "ohlcv": "ohlcv",
        "trades": "trades",
        "orderbook": "order_book",
        "liquidation": "liquidations",
    }

    all_capabilities = get_all_capabilities()
    exchange_support: dict[str, dict[str, dict[str, bool]]] = {}

    for exchange_name, capability in all_capabilities.items():
        exchange_support[exchange_name] = {}
        data_types = capability.get("data_types", {})

        for source_name in sources.keys():
            # Map source to data type
            data_type = source_to_datatype.get(source_name)
            if data_type and data_type in data_types:
                # Get REST/WS support from exchange metadata
                support = data_types[data_type]
                exchange_support[exchange_name][source_name] = {
                    "rest": support.get("rest", False),
                    "ws": support.get("ws", False),
                }
            else:
                # Source not supported by this exchange
                exchange_support[exchange_name][source_name] = {
                    "rest": False,
                    "ws": False,
                }

    return exchange_support


def build_rust_execution_payload(
    plan: PlanResult,
    *,
    dataset_id: int,
    symbol: str,
    timeframe: str,
    source: str,
    requests: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build normalized DAG execution payload for Rust runtime."""
    nodes = {str(node_id): _serialize_ir_node(graph_node.node) for node_id, graph_node in plan.graph.nodes.items()}
    edges = {str(node_id): [int(c) for c in graph_node.children] for node_id, graph_node in plan.graph.nodes.items()}
    return {
        "dataset_id": int(dataset_id),
        "partition": {
            "symbol": symbol,
            "timeframe": timeframe,
            "source": source,
        },
        "graph": {
            "root_id": int(plan.graph.root_id),
            "node_order": [int(n) for n in plan.node_order],
            "nodes": nodes,
            "edges": edges,
        },
        "requests": requests,
        "alignment": {
            "how": plan.alignment.how,
            "fill": plan.alignment.fill,
            "left_fill_value": plan.alignment.left_fill_value,
            "right_fill_value": plan.alignment.right_fill_value,
        },
        "options": {},
    }


def _serialize_ir_node(node: Any) -> dict[str, Any]:
    kind = type(node).__name__
    if kind == "LiteralNode":
        return {"kind": "literal", "value": node.value}
    if kind == "SourceRefNode":
        return {
            "kind": "source_ref",
            "source": node.source,
            "field": node.field,
            "symbol": node.symbol,
            "timeframe": node.timeframe,
            "exchange": node.exchange,
        }
    if kind == "CallNode":
        kwargs: dict[str, str] = {}
        for key, val in node.kwargs.items():
            raw = val.value if hasattr(val, "value") else val
            kwargs[f"kw_{key}"] = str(raw)
        args: dict[str, str] = {}
        for index, arg in enumerate(node.args):
            raw = arg.value if hasattr(arg, "value") else arg
            args[f"arg_{index}"] = str(raw)
        serialized = {
            "kind": "call",
            "name": node.name,
            "output": node.output,
            "args_count": str(len(node.args)),
        }
        serialized.update(kwargs)
        serialized.update(args)
        return serialized
    if kind == "BinaryOpNode":
        return {"kind": "binary_op", "operator": node.operator}
    if kind == "UnaryOpNode":
        return {"kind": "unary_op", "operator": node.operator}
    if kind == "FilterNode":
        return {"kind": "filter"}
    if kind == "AggregateNode":
        return {"kind": "aggregate", "operation": node.operation, "field": node.field}
    if kind == "TimeShiftNode":
        return {"kind": "time_shift", "shift": node.shift, "operation": node.operation}
    return {"kind": "unsupported", "type": kind}
