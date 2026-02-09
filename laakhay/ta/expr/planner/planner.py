"""Planning utilities for expression graphs."""

from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

from ...core import Series
from ...registry.registry import get_global_registry
from ...registry.schemas import IndicatorMetadata
from ..algebra import alignment as alignment_ctx
from ..algebra.alignment import get_policy as _get_alignment_policy
from ..algebra.models import (
    AggregateExpression,
    BinaryOp,
    ExpressionNode,
    FilterExpression,
    Literal,
    SourceExpression,
    TimeShiftExpression,
    UnaryOp,
)
from .builder import build_graph
from .types import (
    AlignmentPolicy,
    DataRequirement,
    Graph,
    PlanResult,
    SignalRequirements,
)


class PlanningError(ValueError):
    """Raised when an expression cannot be planned due to ambiguous or missing metadata."""




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
    time_based_queries: List[str] = []

    # Track lookback requirements per data requirement key (source, field, symbol, exchange, timeframe)
    data_lookbacks: Dict[Tuple[str, str | None, str | None, str | None, str | None], int] = {}

    # Track required lookback per node ID. Root requires 1.
    node_lookbacks: Dict[int, int] = {graph.root_id: 1}

    def merge_field(name: str, timeframe: str | None, lookback: int) -> None:
        key = (name, timeframe)
        prev = fields.get(key, 0)
        if lookback > prev:
            fields[key] = lookback

    def merge_data_requirement(
        source: str,
        field: str,
        symbol: str | None,
        exchange: str | None,
        timeframe: str | None,
        lookback: int,
    ) -> None:
        """Merge data requirement lookback."""
        key = (source, field, symbol, exchange, timeframe)
        prev = data_lookbacks.get(key, 0)
        if lookback > prev:
            data_lookbacks[key] = lookback

    # Traverse in reverse topological order (parent to child)
    # This ensures parent lookback requirements propagate to children before children are processed.
    node_order = _topological_order(graph)[::-1]

    for node_id in node_order:
        node = graph.nodes[node_id]
        expr_node = node.node
        current_lookback = node_lookbacks.get(node_id, 1)

        if _is_indicator_node(expr_node):
            name = expr_node.name
            handle = registry.get(name)
            metadata: IndicatorMetadata | None = handle.schema.metadata if handle else None

            params = expr_node.params if hasattr(expr_node, "params") else {}

            # Check if this indicator has an explicit input_series
            has_input_series = hasattr(expr_node, "input_series") and expr_node.input_series is not None

            if "field" in params:
                # If field is explicitly provided (e.g. mean(volume)), use it.
                required_fields = (params["field"],)
            elif name == "select" and "field" in params:
                required_fields = (params["field"],)
            else:
                required_fields = metadata.required_fields if metadata and metadata.required_fields else ("close",)

            # Determine lookback of this indicator
            indicator_lookback = metadata.default_lookback or 1
            # Special handling for 'select' primitive which is used for terminal fields
            if name == "select":
                field = params.get("field", "close")
                # Source is usually ohlcv for select, but could be overridden if select is used on trades etc.
                # However, for terminal SelectNodes in the graph, it's the default context.
                merge_data_requirement(
                    "ohlcv",
                    field,
                    None,
                    None,
                    None,
                    current_lookback,
                )
                # Also merge into legacy fields for backward compatibility
                merge_field(field, None, current_lookback)

            if metadata and metadata.lookback_params:
                collected: List[int] = []
                for param in metadata.lookback_params:
                    value = params.get(param)
                    if isinstance(value, int | float):
                        collected.append(int(value))
                if collected:
                    indicator_lookback = max(collected)

            # Total lookback required from dependencies of this indicator
            # Formula: parent_required_lookback + indicator_window - 1
            total_required = current_lookback + indicator_lookback - 1

            if node.children:
                # Propagate requirement to all children (input_series and param-based inputs)
                for child_id in node.children:
                    node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), total_required)
            else:
                # Require standard fields if no inputs provided
                for field_name in required_fields:
                    merge_field(field_name, None, max(total_required, 1))

        elif isinstance(expr_node, Literal):
            if isinstance(expr_node.value, Series):
                merge_field("close", expr_node.value.timeframe, current_lookback)

        elif isinstance(expr_node, BinaryOp):
            # Propagate requirement to both operands
            for child_id in node.children:
                node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), current_lookback)

        elif isinstance(expr_node, UnaryOp):
            # Propagate requirement to operand
            for child_id in node.children:
                node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), current_lookback)

        elif isinstance(expr_node, SourceExpression):
            # Handle SourceExpression - map to DataRequirement
            # For OHLCV sources, also create FieldRequirement for backward compatibility
            if expr_node.source == "ohlcv" and expr_node.symbol is None and expr_node.exchange is None:
                # Map OHLCV fields to legacy FieldRequirement
                field_name = expr_node.field
                if field_name in ("price", "close"):
                    field_name = "close"
                elif field_name in ("open", "high", "low", "volume"):
                    pass  # Use as-is
                else:
                    # For derived fields, default to close
                    field_name = "close"
                merge_field(field_name, expr_node.timeframe, current_lookback)

            # Track data requirement
            merge_data_requirement(
                expr_node.source,
                expr_node.field,
                expr_node.symbol,
                expr_node.exchange,
                expr_node.timeframe,
                current_lookback,
            )

        elif isinstance(expr_node, TimeShiftExpression):
            # Track time-based queries
            time_based_queries.append(expr_node.shift)
            # Propagate requirement to child series
            for child_id in node.children:
                node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), current_lookback)

        elif isinstance(expr_node, FilterExpression):
            # Propagate requirement to both series and condition
            for child_id in node.children:
                node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), current_lookback)

        elif isinstance(expr_node, AggregateExpression):
            # Propagate requirement to series
            for child_id in node.children:
                node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), current_lookback)

            # Keep track of aggregation params for this node (though we don't return them per node here)
            # SignalRequirements currently doesn't store per-node aggregation params.

    # Map legacy field requirements to canonical DataRequirements
    for (name, timeframe), lookback in fields.items():
        merge_data_requirement(
            "ohlcv",
            name,
            None,  # symbol
            None,  # exchange
            timeframe,
            lookback
        )

    # Convert data_lookbacks to DataRequirement objects
    data_requirements = [
        DataRequirement(
            source=source,
            field=field,
            symbol=symbol,
            exchange=exchange,
            timeframe=timeframe,
            min_lookback=lookback,
        )
        for (source, field, symbol, exchange, timeframe), lookback in sorted(
            data_lookbacks.items(),
            key=lambda item: (item[0][0], item[0][1] or "", item[0][2] or "", item[0][3] or "", item[0][4] or ""),
        )
    ]

    return SignalRequirements(
        data_requirements=tuple(data_requirements),
        time_based_queries=tuple(time_based_queries),
    )


__all__ = [
    "alignment",
    "get_alignment_policy",
    "plan_expression",
    "compute_plan",
]
