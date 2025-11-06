"""Graph planning type definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..expressions.models import ExpressionNode


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
class SignalRequirements:
    fields: tuple[FieldRequirement, ...]
    derived: tuple[DerivedRequirement, ...] = ()


@dataclass(frozen=True)
class PlanResult:
    graph: Graph
    node_order: tuple[int, ...]
    requirements: SignalRequirements
    alignment: AlignmentPolicy

    @property
    def graph_hash(self) -> str:
        return self.graph.hash
