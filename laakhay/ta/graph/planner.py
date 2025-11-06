"""Planning utilities for expression graphs."""

from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

from ..core import Series
from ..expressions import alignment as alignment_ctx
from ..expressions.alignment import get_policy as _get_alignment_policy
from ..expressions.models import BinaryOp, ExpressionNode, Literal, UnaryOp
from ..registry.registry import get_global_registry
from ..registry.schemas import IndicatorMetadata
from .builder import build_graph
from .types import (
    AlignmentPolicy,
    DerivedRequirement,
    FieldRequirement,
    Graph,
    PlanResult,
    SignalRequirements,
)


def alignment(
    *,
    how: str | None = None,
    fill: str | None = None,
    left_fill_value: Any | None = None,
    right_fill_value: Any | None = None,
):
    """Proxy to the expression alignment context manager."""
    return alignment_ctx.alignment(
        how=how,
        fill=fill,
        left_fill_value=left_fill_value,
        right_fill_value=right_fill_value,
    )


def get_alignment_policy() -> AlignmentPolicy:
    how, fill, left_fill_value, right_fill_value = _get_alignment_policy()
    return AlignmentPolicy(
        how=how,
        fill=fill,
        left_fill_value=left_fill_value,
        right_fill_value=right_fill_value,
    )


def _is_indicator_node(node: ExpressionNode) -> bool:
    return node.__class__.__name__ == "IndicatorNode" and hasattr(node, "name") and hasattr(node, "params")


def plan_expression(root: ExpressionNode) -> PlanResult:
    graph = build_graph(root)
    return compute_plan(graph)


def compute_plan(graph: Graph) -> PlanResult:
    alignment_policy = get_alignment_policy()
    node_order = _topological_order(graph)
    requirements = _collect_requirements(graph)
    return PlanResult(
        graph=graph,
        node_order=node_order,
        requirements=requirements,
        alignment=alignment_policy,
    )


def _topological_order(graph: Graph) -> tuple[int, ...]:
    order: List[int] = []
    visited: Set[int] = set()

    def dfs(node_id: int) -> None:
        if node_id in visited:
            return
        visited.add(node_id)
        for child in graph.nodes[node_id].children:
            dfs(child)
        order.append(node_id)

    dfs(graph.root_id)
    return tuple(order)


def _collect_requirements(graph: Graph) -> SignalRequirements:
    registry = get_global_registry()
    fields: Dict[Tuple[str, str | None], int] = {}
    derived: List[DerivedRequirement] = []

    def merge_field(name: str, timeframe: str | None, lookback: int) -> None:
        key = (name, timeframe)
        prev = fields.get(key, 0)
        if lookback > prev:
            fields[key] = lookback

    for node in graph.nodes.values():
        expr_node = node.node
        if _is_indicator_node(expr_node):
            name = expr_node.name
            handle = registry.get(name)
            metadata: IndicatorMetadata | None = handle.schema.metadata if handle else None

            params = expr_node.params if hasattr(expr_node, "params") else {}

            if name == "select" and "field" in params:
                required_fields = (params["field"],)
            else:
                required_fields = metadata.required_fields if metadata and metadata.required_fields else ("close",)

            lookback = metadata.default_lookback or 1

            if metadata and metadata.lookback_params:
                collected: List[int] = []
                for param in metadata.lookback_params:
                    value = params.get(param)
                    if isinstance(value, int):
                        collected.append(int(value))
                if collected:
                    lookback = max(collected)

            for field_name in required_fields:
                merge_field(field_name, None, max(lookback, 1))

        elif isinstance(expr_node, Literal):
            if isinstance(expr_node.value, Series):
                merge_field("close", expr_node.value.timeframe, 1)
        elif isinstance(expr_node, UnaryOp):
            continue
        elif isinstance(expr_node, BinaryOp):
            continue

    field_requirements = tuple(
        FieldRequirement(name=name, timeframe=timeframe, min_lookback=lookback)
        for (name, timeframe), lookback in sorted(fields.items(), key=lambda item: (item[0][0], item[0][1] or ""))
    )
    return SignalRequirements(fields=field_requirements, derived=tuple(derived))


__all__ = [
    "alignment",
    "get_alignment_policy",
    "plan_expression",
    "compute_plan",
]
