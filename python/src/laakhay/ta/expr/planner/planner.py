"""Planning utilities for expression graphs."""

from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

from ...core import Series
from ...registry.registry import get_global_registry
from ..algebra import alignment as alignment_ctx
from ..algebra.alignment import get_policy as _get_alignment_policy
from ..ir.nodes import (
    AggregateNode,
    BinaryOpNode,
    CallNode,
    CanonicalExpression,
    FilterNode,
    LiteralNode,
    SourceRefNode,
    TimeShiftNode,
    UnaryOpNode,
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


def plan_expression(root: CanonicalExpression) -> PlanResult:
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
    time_based_queries: List[str] = []

    # Canonical: track lookback per (source, field, symbol, exchange, timeframe)
    data_lookbacks: Dict[Tuple[str, str | None, str | None, str | None, str | None], int] = {}

    # Track required lookback per node ID. Root requires 1.
    node_lookbacks: Dict[int, int] = {graph.root_id: 1}

    def _merge_ohlcv_field(field: str, timeframe: str | None, lookback: int) -> None:
        """Merge an OHLCV field requirement (source=ohlcv, symbol/exchange unspecified)."""
        merge_data_requirement("ohlcv", field, None, None, timeframe, lookback)

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

        if isinstance(expr_node, CallNode):
            name = expr_node.name
            handle = registry.get(name)
            if not handle:
                continue
            spec = handle.indicator_spec
            semantics = spec.semantics
            param_defs = [p.name for p in handle.schema.parameters.values() if p.name.lower() not in {"ctx", "context"}]

            params = {}
            for k, v in expr_node.kwargs.items():
                params[k] = v.value if isinstance(v, LiteralNode) else v

            has_input_series = len(expr_node.args) > 0 and not isinstance(expr_node.args[0], LiteralNode)
            arg_offset = 1 if has_input_series else 0
            input_series_param = semantics.input_series_param or (spec.inputs[0].name if spec.inputs else None)
            param_start = 1 if (has_input_series and param_defs and param_defs[0] == input_series_param) else 0
            for idx, arg in enumerate(expr_node.args[arg_offset:]):
                param_idx = param_start + idx
                if param_idx >= len(param_defs):
                    break
                if not isinstance(arg, LiteralNode):
                    continue
                param_name = param_defs[param_idx]
                if param_name not in params:
                    params[param_name] = arg.value

            if "field" in params:
                required_fields = (params["field"],)
            elif name == "select":
                sel_field = params.get("field", "close")
                if "field" not in params and len(expr_node.args) > 0:
                    val = expr_node.args[0]
                    if isinstance(val, LiteralNode) and isinstance(val.value, str):
                        sel_field = val.value
                    elif isinstance(val, str):
                        sel_field = val
                required_fields = (sel_field,)
            else:
                required_fields = semantics.required_fields or (
                    (spec.inputs[0].default_field,) if spec.inputs and spec.inputs[0].default_field else ("close",)
                )

            indicator_lookback = semantics.default_lookback or 1
            # Special handling for 'select' primitive which is used for terminal fields
            if name == "select":
                field = required_fields[0]
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

            if semantics.lookback_params:
                collected: List[int] = []
                for param in semantics.lookback_params:
                    value = params.get(param)
                    if isinstance(value, int | float):
                        collected.append(int(value))
                if collected:
                    indicator_lookback = max(collected)

            # Total lookback required from dependencies of this indicator
            # Formula: parent_required_lookback + indicator_window - 1
            total_required = current_lookback + indicator_lookback - 1

            if not has_input_series:
                # Require standard OHLCV fields if no inputs provided
                for field_name in required_fields:
                    _merge_ohlcv_field(field_name, None, max(total_required, 1))

            # Propagate requirement to all children (input_series and param-based inputs)
            for child_id in node.children:
                node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), total_required)

        elif isinstance(expr_node, LiteralNode):
            if isinstance(expr_node.value, Series):
                _merge_ohlcv_field("close", expr_node.value.timeframe, current_lookback)

        elif isinstance(expr_node, BinaryOpNode):
            # Propagate requirement to both operands
            for child_id in node.children:
                node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), current_lookback)

        elif isinstance(expr_node, UnaryOpNode):
            # Propagate requirement to operand
            for child_id in node.children:
                node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), current_lookback)

        elif isinstance(expr_node, SourceRefNode):
            # Track canonical data requirement
            merge_data_requirement(
                expr_node.source,
                expr_node.field,
                expr_node.symbol,
                expr_node.exchange,
                expr_node.timeframe,
                current_lookback,
            )

        elif isinstance(expr_node, TimeShiftNode):
            # Track time-based queries
            time_based_queries.append(expr_node.shift)
            # Propagate requirement to child series
            for child_id in node.children:
                node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), current_lookback)

        elif isinstance(expr_node, FilterNode):
            # Propagate requirement to both series and condition
            for child_id in node.children:
                node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), current_lookback)

        elif isinstance(expr_node, AggregateNode):
            # Propagate requirement to series
            for child_id in node.children:
                node_lookbacks[child_id] = max(node_lookbacks.get(child_id, 0), current_lookback)

            # Keep track of aggregation params for this node (though we don't return them per node here)
            # SignalRequirements currently doesn't store per-node aggregation params.

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
