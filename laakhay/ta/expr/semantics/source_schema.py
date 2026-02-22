"""Canonical source/field schema for expression parsing and validation."""

from __future__ import annotations

from dataclasses import dataclass, field

# -----------------------------------------------------------------------------
# Structured source definitions (struct-like)
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceDef:
    """Defines a data source with its name, description, and available fields."""

    name: str
    description: str
    field_names: frozenset[str] = field(default_factory=frozenset)

    def __contains__(self, field_name: str) -> bool:
        return field_name.lower() in self.field_names

    def __iter__(self):
        return iter(sorted(self.field_names))


# OHLCV candlestick data
OHLCV = SourceDef(
    name="ohlcv",
    description="OHLCV candlestick data",
    field_names=frozenset(
        {
            "open",
            "high",
            "low",
            "close",
            "volume",
            "price",  # alias for close
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
)

# Trade aggregation data
TRADES = SourceDef(
    name="trades",
    description="Trade aggregation data",
    field_names=frozenset(
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
)

# Order book snapshot data
ORDERBOOK = SourceDef(
    name="orderbook",
    description="Order book snapshot data",
    field_names=frozenset(
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
            "bid",
            "ask",
            "bid_size",
            "ask_size",
        }
    ),
)

# Liquidation aggregation data
LIQUIDATION = SourceDef(
    name="liquidation",
    description="Liquidation aggregation data",
    field_names=frozenset(
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
)

# Registry of all source definitions
SOURCE_DEFS: dict[str, SourceDef] = {
    OHLCV.name: OHLCV,
    TRADES.name: TRADES,
    ORDERBOOK.name: ORDERBOOK,
    LIQUIDATION.name: LIQUIDATION,
}

SOURCE_FIELDS: dict[str, frozenset[str]] = {src.name: src.field_names for src in SOURCE_DEFS.values()}

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

# Derived from SourceDef structs
SOURCE_DESCRIPTIONS: dict[str, str] = {src.name: src.description for src in SOURCE_DEFS.values()}


def canonical_select_field(field: str) -> str:
    lowered = field.lower()
    return SELECT_FIELD_ALIASES.get(lowered, lowered)


def valid_source_fields(source: str) -> frozenset[str]:
    return SOURCE_FIELDS.get(source.lower(), frozenset())


def is_valid_source_field(source: str, field: str | None) -> bool:
    if field is None:
        return True
    return field.lower() in valid_source_fields(source)


# -----------------------------------------------------------------------------
# Explicit source callables (ohlcv, trades, orderbook, liquidation)
# -----------------------------------------------------------------------------


def _make_source(src_def: SourceDef):
    """Create a callable that selects a field from a named data source."""

    def _source(field_name: str):
        from ..algebra import Expression
        from ..ir.nodes import SourceRefNode

        canonical = canonical_select_field(field_name.lower()) if src_def.name == "ohlcv" else field_name.lower()
        if canonical not in src_def:
            raise ValueError(
                f"Field {field_name!r} is not valid for source {src_def.name!r}. "
                f"Valid fields: {sorted(src_def.field_names)}"
            )
        return Expression(
            SourceRefNode(
                source=src_def.name,
                field=canonical,
                symbol=None,
                exchange=None,
                timeframe=None,
            )
        )

    _source.__name__ = src_def.name
    _source.__doc__ = f"{src_def.description}. Valid fields: {sorted(src_def.field_names)}"
    return _source


# Explicitly defined sources – first-class API for data source selection
ohlcv = _make_source(OHLCV)
trades = _make_source(TRADES)
orderbook = _make_source(ORDERBOOK)
liquidation = _make_source(LIQUIDATION)
