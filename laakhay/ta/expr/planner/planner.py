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
    data_requirements: List[DataRequirement] = []
    required_sources: Set[str] = set()
    required_exchanges: Set[str] = set()
    time_based_queries: List[str] = []

    # Track lookback requirements per data requirement key
    data_lookbacks: Dict[Tuple[str, str | None, str | None, str | None], int] = {}

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

    for node in graph.nodes.values():
        expr_node = node.node
        if _is_indicator_node(expr_node):
            name = expr_node.name
            handle = registry.get(name)
            metadata: IndicatorMetadata | None = handle.schema.metadata if handle else None

            params = expr_node.params if hasattr(expr_node, "params") else {}

            # Check if this indicator has an explicit input_series
            has_input_series = hasattr(expr_node, "input_series") and expr_node.input_series is not None

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

            # If indicator has explicit input_series, don't require default fields
            # The input_series will be processed as a child node and its dependencies tracked
            if not has_input_series:
                for field_name in required_fields:
                    merge_field(field_name, None, max(lookback, 1))

            # If this indicator uses a SourceExpression (either directly or via input_series),
            # increase its lookback. The input_series will be processed as a child, so we
            # need to increase lookback for data requirements that match the indicator's needs.
            # For indicators with input_series, the lookback applies to the input_series source.
            for key in list(data_lookbacks.keys()):
                source, field, symbol, exchange, timeframe = key
                # If this indicator requires the field we're tracking, increase lookback
                if field in required_fields or (field == "close" and "close" in required_fields):
                    data_lookbacks[key] = max(data_lookbacks[key], lookback)

        elif isinstance(expr_node, Literal):
            if isinstance(expr_node.value, Series):
                merge_field("close", expr_node.value.timeframe, 1)
        elif isinstance(expr_node, UnaryOp):
            continue
        elif isinstance(expr_node, BinaryOp):
            continue
        elif isinstance(expr_node, SourceExpression):
            # Handle SourceExpression - map to DataRequirement
            # For OHLCV sources, also create FieldRequirement for backward compatibility
            if expr_node.source == "ohlcv":
                # Map OHLCV fields to legacy FieldRequirement
                field_name = expr_node.field
                if field_name in ("price", "close"):
                    field_name = "close"
                elif field_name in ("open", "high", "low", "volume"):
                    pass  # Use as-is
                else:
                    # For derived fields, default to close
                    field_name = "close"
                merge_field(field_name, expr_node.timeframe, 1)

            # Track data requirement (lookback will be merged later)
            merge_data_requirement(
                expr_node.source,
                expr_node.field,
                expr_node.symbol,
                expr_node.exchange,
                expr_node.timeframe,
                1,  # Base lookback, will be increased by indicators
            )
            required_sources.add(expr_node.source)
            if expr_node.exchange:
                required_exchanges.add(expr_node.exchange)

        elif isinstance(expr_node, TimeShiftExpression):
            # Track time-based queries
            time_based_queries.append(expr_node.shift)
            # Parse shift to determine lookback requirement
            # e.g., "24h_ago" needs 24 hours of historical data
            # The underlying series requirement will be collected recursively
            # For now, we just track the shift pattern

        elif isinstance(expr_node, FilterExpression):
            # For filters, we need to collect requirements from both series and condition
            # The filter doesn't change the data requirement, but we need to track it
            # Requirements from series and condition will be collected recursively
            # For now, we just pass through - the recursive collection will handle it
            pass

        elif isinstance(expr_node, AggregateExpression):
            # For aggregations, we need to collect requirements from the series
            # The aggregation_params will be populated based on the operation
            # For aggregations like trades.sum(amount), we need to track:
            # - The source (trades)
            # - The field being aggregated (amount)
            # - The operation (sum, count, avg, etc.)
            # Requirements from series will be collected recursively
            # We'll extract aggregation params from the expression structure
            aggregation_params = {
                "operation": expr_node.operation,
            }
            if expr_node.field:
                aggregation_params["field"] = expr_node.field

            # Try to find the underlying SourceExpression to create a DataRequirement
            # with aggregation params
            # This is a simplified approach - in practice, we'd need to traverse
            # the series expression to find SourceExpression nodes
            # For now, we'll rely on recursive collection

    field_requirements = tuple(
        FieldRequirement(name=name, timeframe=timeframe, min_lookback=lookback)
        for (name, timeframe), lookback in sorted(fields.items(), key=lambda item: (item[0][0], item[0][1] or ""))
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
        fields=field_requirements,
        derived=tuple(derived),
        data_requirements=tuple(data_requirements),
        required_sources=tuple(sorted(required_sources)),
        required_exchanges=tuple(sorted(required_exchanges)),
        time_based_queries=tuple(time_based_queries),
    )


__all__ = [
    "alignment",
    "get_alignment_policy",
    "plan_expression",
    "compute_plan",
]
