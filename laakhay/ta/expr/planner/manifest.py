"""Capability manifest generation for strategies API."""

from __future__ import annotations

import ast
import inspect
from dataclasses import fields
from typing import Any

from ...core.context import (
    LiquidationContext,
    OHLCVContext,
    OrderBookContext,
    TradeContext,
)
from ...registry.registry import get_global_registry


def generate_capability_manifest() -> dict[str, Any]:
    """Generate capability manifest for /api/v1/strategies/capabilities.

    This manifest describes:
    - Available data sources (ohlcv, trades, orderbook, liquidation)
    - Available fields per source
    - Available indicators
    - Available operators
    - Expression syntax examples
    - Exchange-specific source support (merged with laakhay-data metadata)

    Returns:
        Dictionary with capability information for frontend/backend consumption.
    """
    registry = get_global_registry()

    # Get all registered indicators
    indicators = []
    for name in registry.list_all_names():
        handle = registry.get(name)
        if handle:
            schema = handle.schema
            indicators.append(
                {
                    "name": name,
                    "parameters": {
                        param_name: {
                            "type": param_schema.type.__name__ if param_schema.type else "unknown",
                            "required": param_schema.required,
                            "default": param_schema.default,
                        }
                        for param_name, param_schema in schema.parameters.items()
                        if param_name.lower() not in ("ctx", "context")
                    },
                    "outputs": list(schema.outputs.keys()) if schema.outputs else [],
                }
            )

    # Extract source fields from parser's validation logic
    sources = _extract_source_fields_from_parser()

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
            "BTC/USDT.price > 50000",
            "BTC/USDT.trades.volume > 1000000",
            "BTC/USDT.orderbook.imbalance > 0.5",
        ],
        "filters": [
            "BTC/USDT.trades.filter(amount > 1000000).count > 10",
        ],
        "aggregations": [
            "BTC/USDT.trades.sum(amount) > 50000000",
            "BTC/USDT.trades.count > 100",
        ],
        "time_shifts": [
            "BTC/USDT.price.24h_ago < BTC/USDT.price",
            "BTC/USDT.volume.change_pct_24h > 10",
        ],
    }

    return {
        "sources": sources,
        "exchange_source_support": exchange_source_support,
        "indicators": sorted(indicators, key=lambda x: x["name"]),
        "operators": operators,
        "examples": examples,
        "version": "1.2.0",  # Version for multi-source support and explicit indicator inputs
        "dsl_version": "1.0.0",  # DSL syntax version
        "features": {
            "multi_source": True,
            "explicit_indicator_inputs": True,
            "filters": True,
            "aggregations": True,
            "time_shifts": True,
        },
    }


def _extract_source_fields_from_parser() -> dict[str, dict[str, Any]]:
    """Extract source fields from parser's validation method using AST parsing."""
    # Lazy import to avoid circular dependencies
    from ..dsl.parser import ExpressionParser

    try:
        parser = ExpressionParser()
        # Parse the AST of the method to find the source_fields dict
        method_source = inspect.getsource(parser._validate_attribute_combination)
        tree = ast.parse(method_source)

        # Find the source_fields dict assignment
        source_fields_dict = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "source_fields":
                        if isinstance(node.value, ast.Dict):
                            # Extract dict keys and values
                            for key_node, value_node in zip(node.value.keys, node.value.values, strict=False):
                                if isinstance(key_node, ast.Constant) and isinstance(value_node, ast.Set):
                                    source_name = key_node.value
                                    field_set = {el.value for el in value_node.elts if isinstance(el, ast.Constant)}
                                    source_fields_dict[source_name] = sorted(field_set)

        if source_fields_dict:
            # Build sources dict with descriptions from context classes
            sources = {}
            source_descriptions = {
                "ohlcv": "OHLCV candlestick data",
                "trades": "Trade aggregation data",
                "orderbook": "Order book snapshot data",
                "liquidation": "Liquidation aggregation data",
            }

            for source_name, fields_list in source_fields_dict.items():
                sources[source_name] = {
                    "fields": fields_list,
                    "description": source_descriptions.get(source_name, f"{source_name} data"),
                }
            return sources
    except Exception:
        pass

    # Fallback: extract from context classes (but this misses derived fields like hlc3, ohlc4)
    # For now, we'll use context classes and note that derived fields are parser-specific
    return _extract_source_fields_from_contexts()


def _extract_source_fields_from_contexts() -> dict[str, dict[str, Any]]:
    """Extract source fields from context class dataclass fields.

    Note: This extracts base fields from context classes. Derived fields (like hlc3, ohlc4)
    are defined in the parser's validation logic and should be extracted from there.
    """
    context_mapping = {
        "ohlcv": (OHLCVContext, "OHLCV candlestick data"),
        "trades": (TradeContext, "Trade aggregation data"),
        "orderbook": (OrderBookContext, "Order book snapshot data"),
        "liquidation": (LiquidationContext, "Liquidation aggregation data"),
    }

    # Derived fields that are parser-specific (not in context classes)
    derived_fields = {
        "ohlcv": [
            "hlc3",  # Typical price: (high + low + close) / 3
            "ohlc4",  # Average price: (open + high + low + close) / 4
            "hl2",  # Mid price: (high + low) / 2
            "typical_price",  # Alias for hlc3
            "weighted_close",  # Alias for ohlc4
            "median_price",  # Alias for hl2
            "range",  # High - Low
            "upper_wick",  # High - max(Open, Close)
            "lower_wick",  # min(Open, Close) - Low
        ],
    }

    sources = {}
    for source_name, (context_class, description) in context_mapping.items():
        # Get all field names from the dataclass
        field_names = [field.name for field in fields(context_class) if not field.name.startswith("_")]

        # Add derived fields if any
        if source_name in derived_fields:
            field_names.extend(derived_fields[source_name])

        sources[source_name] = {
            "fields": sorted(set(field_names)),  # Remove duplicates
            "description": description,
        }

    return sources


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
