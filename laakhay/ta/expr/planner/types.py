"""Graph planning type definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..algebra.models import ExpressionNode


@dataclass(frozen=True)
class GraphNode:
    """Node inside a canonical expression graph."""

    id: int
    node: ExpressionNode
    children: tuple[int, ...]
    signature: tuple[Any, ...]
    hash: str


@dataclass(frozen=True)
class Graph:
    """Canonical graph representation for an expression."""

    root_id: int
    nodes: dict[int, GraphNode]
    hash: str


@dataclass(frozen=True)
class AlignmentPolicy:
    how: str = "inner"
    fill: str = "none"
    left_fill_value: Any | None = None
    right_fill_value: Any | None = None

    def cache_key(self) -> tuple[Any, ...]:
        return (self.how, self.fill, self.left_fill_value, self.right_fill_value)


@dataclass(frozen=True)
class FieldRequirement:
    name: str
    timeframe: str | None
    min_lookback: int


@dataclass(frozen=True)
class DerivedRequirement:
    name: str
    params: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True)
class DataRequirement:
    """Requirement for a specific data source."""

    source: str  # 'ohlcv', 'trades', 'orderbook', 'liquidation'
    field: str  # 'price', 'volume', 'count', 'imbalance', etc.
    symbol: str | None = None  # None means "any symbol in scope"
    exchange: str | None = None  # None means "any exchange"
    timeframe: str | None = None  # None means "default timeframe"
    min_lookback: int = 1
    aggregation_params: dict[str, Any] | None = None  # For filters/aggregations


@dataclass(frozen=True)
class SignalRequirements:
    fields: tuple[FieldRequirement, ...]
    derived: tuple[DerivedRequirement, ...] = ()
    data_requirements: tuple[DataRequirement, ...] = ()
    required_sources: tuple[str, ...] = ()
    required_exchanges: tuple[str, ...] = ()
    time_based_queries: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlanResult:
    graph: Graph
    node_order: tuple[int, ...]
    requirements: SignalRequirements
    alignment: AlignmentPolicy

    @property
    def graph_hash(self) -> str:
        return self.graph.hash

    def to_dict(self) -> dict[str, Any]:
        """Serialize PlanResult to a dictionary for backend/frontend consumption."""
        return {
            "graph_hash": self.graph_hash,
            "node_order": list(self.node_order),
            "requirements": {
                "fields": [
                    {
                        "name": field.name,
                        "timeframe": field.timeframe,
                        "min_lookback": field.min_lookback,
                    }
                    for field in self.requirements.fields
                ],
                "derived": [
                    {
                        "name": derived.name,
                        "params": dict(derived.params),
                    }
                    for derived in self.requirements.derived
                ],
                "data_requirements": [
                    {
                        "source": req.source,
                        "field": req.field,
                        "symbol": req.symbol,
                        "exchange": req.exchange,
                        "timeframe": req.timeframe,
                        "min_lookback": req.min_lookback,
                        "aggregation_params": req.aggregation_params,
                    }
                    for req in self.requirements.data_requirements
                ],
                "required_sources": list(self.requirements.required_sources),
                "required_exchanges": list(self.requirements.required_exchanges),
                "time_based_queries": list(self.requirements.time_based_queries),
            },
            "alignment": {
                "how": self.alignment.how,
                "fill": self.alignment.fill,
                "left_fill_value": self.alignment.left_fill_value,
                "right_fill_value": self.alignment.right_fill_value,
            },
        }
