"""Canonical source/field schema for expression parsing and validation."""

from __future__ import annotations

SOURCE_FIELDS: dict[str, frozenset[str]] = {
    "ohlcv": frozenset(
        {
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
        }
    ),
    "trades": frozenset(
        {
            "price",
            "volume",
            "count",
            "buy_volume",
            "sell_volume",
            "large_count",
            "whale_count",
            "avg_price",
            "vwap",
            "amount",
            "side",
            "id",
            "timestamp",
        }
    ),
    "orderbook": frozenset(
        {
            "best_bid",
            "best_ask",
            "spread",
            "spread_bps",
            "mid_price",
            "bid_depth",
            "ask_depth",
            "imbalance",
            "pressure",
            # Backward-compatible aliases seen in older validators/tests.
            "bid",
            "ask",
            "bid_size",
            "ask_size",
        }
    ),
    "liquidation": frozenset(
        {
            "count",
            "volume",
            "value",
            "long_count",
            "short_count",
            "long_value",
            "short_value",
            "large_count",
            "large_value",
            "price",
            "amount",
            "side",
            "id",
            "timestamp",
        }
    ),
}

KNOWN_SOURCES: frozenset[str] = frozenset(SOURCE_FIELDS.keys())

SELECT_FIELD_ALIASES: dict[str, str] = {
    "o": "open",
    "h": "high",
    "l": "low",
    "c": "close",
    "v": "volume",
}

VALID_SELECT_FIELDS: frozenset[str] = frozenset(
    {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "hlc3",
        "ohlc4",
        "hl2",
        "range",
        "upper_wick",
        "lower_wick",
        "typical_price",
        "weighted_close",
        "median_price",
        "price",
        *SELECT_FIELD_ALIASES.keys(),
    }
)

# Bare identifiers in expressions that should resolve to a source selector.
DEFAULT_SOURCE_FIELDS: frozenset[str] = frozenset(
    {
        "close",
        "high",
        "low",
        "open",
        "volume",
        "price",
        "amount",
        "count",
        "side",
        "bid",
        "ask",
        "hlc3",
        "ohlc4",
        "hl2",
        "typical_price",
        "weighted_close",
        "median_price",
        "range",
        "upper_wick",
        "lower_wick",
        *SELECT_FIELD_ALIASES.keys(),
    }
)

SOURCE_DESCRIPTIONS: dict[str, str] = {
    "ohlcv": "OHLCV candlestick data",
    "trades": "Trade aggregation data",
    "orderbook": "Order book snapshot data",
    "liquidation": "Liquidation aggregation data",
}


def canonical_select_field(field: str) -> str:
    lowered = field.lower()
    return SELECT_FIELD_ALIASES.get(lowered, lowered)


def valid_source_fields(source: str) -> frozenset[str]:
    return SOURCE_FIELDS.get(source.lower(), frozenset())


def is_valid_source_field(source: str, field: str | None) -> bool:
    if field is None:
        return True
    return field.lower() in valid_source_fields(source)
