"""Capability manifest generation for strategies API."""

from __future__ import annotations

from typing import Any

from ...registry.registry import get_global_registry


def generate_capability_manifest() -> dict[str, Any]:
    """Generate capability manifest for /api/v1/strategies/capabilities.

    This manifest describes:
    - Available data sources (ohlcv, trades, orderbook, liquidation)
    - Available fields per source
    - Available indicators
    - Available operators
    - Expression syntax examples

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

    # Define available sources and their fields
    sources = {
        "ohlcv": {
            "fields": [
                "price",
                "close",
                "open",
                "high",
                "low",
                "volume",
                "hlc3",
                "ohlc4",
                "hl2",
                "typical_price",
                "weighted_close",
                "median_price",
                "range",
                "upper_wick",
                "lower_wick",
            ],
            "description": "OHLCV candlestick data",
        },
        "trades": {
            "fields": [
                "volume",
                "count",
                "buy_volume",
                "sell_volume",
                "large_count",
                "whale_count",
                "avg_price",
                "vwap",
                "amount",
            ],
            "description": "Trade aggregation data",
        },
        "orderbook": {
            "fields": [
                "best_bid",
                "best_ask",
                "spread",
                "spread_bps",
                "mid_price",
                "bid_depth",
                "ask_depth",
                "imbalance",
                "pressure",
            ],
            "description": "Order book snapshot data",
        },
        "liquidation": {
            "fields": [
                "count",
                "volume",
                "value",
                "long_count",
                "short_count",
                "long_value",
                "short_value",
                "large_count",
                "large_value",
            ],
            "description": "Liquidation aggregation data",
        },
    }

    # Define available operators
    operators = {
        "arithmetic": ["+", "-", "*", "/", "%", "**"],
        "comparison": [">", ">=", "<", "<=", "==", "!="],
        "logical": ["and", "or", "not"],
    }

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
        "indicators": sorted(indicators, key=lambda x: x["name"]),
        "operators": operators,
        "examples": examples,
        "version": "1.0.0",
    }
