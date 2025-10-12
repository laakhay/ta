from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .io import TAInput, TAOutput
from .registry import get_indicator


class CyclicDependencyError(Exception):
    """Raised when a circular dependency is detected in the indicator graph."""
    pass


class IndicatorNotFoundError(Exception):
    """Raised when a requested indicator is not registered."""
    pass


def stable_params_hash(params: dict[str, Any]) -> str:
    """
    Canonical, short hash for parameter dicts to key cached outputs.
    """
    payload = json.dumps(params or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class ComputeRequest(BaseModel):
    """
    Target indicator evaluation request for a single timeframe (multi-asset).
    """
    indicator_name: str
    params: dict[str, Any] = Field(default_factory=dict)
    symbols: list[str]
    eval_ts: datetime | None = None


class PlanNode(BaseModel):
    """
    A node in the execution DAG.
    kind == "raw": key describes raw slice node (e.g., ("price","close","BTCUSDT"))
    kind == "indicator": key describes computed outputs (e.g., ("rsi","<hash>","BTCUSDT"))
    """
    kind: Literal["raw", "indicator"]
    key: tuple[str, ...]
    # Optional for indicator nodes; raw nodes generally won't need it here.
    params: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    nodes: list[PlanNode]  # topologically sorted (deps come first)


def build_execution_plan(req: ComputeRequest) -> ExecutionPlan:
    """
    Resolve dependencies from INDICATORS[req.indicator_name].requirements() into a DAG
    for the requested symbols (single timeframe). Topologically sort nodes.

    Algorithm:
    1. Get target indicator class from registry
    2. Build dependency graph recursively (DFS)
    3. Topologically sort (Kahn's algorithm)
    4. Detect cycles and raise CyclicDependencyError

    Returns:
        ExecutionPlan with topologically sorted nodes (dependencies first)
    """
    # 1. Get target indicator class
    target_cls = get_indicator(req.indicator_name)
    if not target_cls:
        raise IndicatorNotFoundError(
            f"Indicator '{req.indicator_name}' not found in registry. "
            f"Register it with @register decorator."
        )

    # 2. Build dependency graph (adjacency list)
    graph: dict[tuple[str, ...], list[tuple[str, ...]]] = {}
    visited: set[tuple[str, ...]] = set()

    def visit_indicator(ind_name: str, params: dict[str, Any], symbols: list[str]) -> None:
        """Recursively visit indicator and its dependencies."""
        ind_cls = get_indicator(ind_name)
        if not ind_cls:
            raise IndicatorNotFoundError(f"Indicator '{ind_name}' not found")

        reqs = ind_cls.requirements()
        p_hash = stable_params_hash(params)

        # Process each symbol
        for symbol in symbols:
            # Create node key for this indicator instance
            ind_key = ("indicator", ind_name, p_hash, symbol)

            if ind_key in visited:
                continue
            visited.add(ind_key)

            # Initialize adjacency list
            if ind_key not in graph:
                graph[ind_key] = []

            # Add raw data dependencies
            for raw_dep in reqs.raw:
                dep_symbols = raw_dep.symbols if raw_dep.symbols else [symbol]
                for dep_symbol in dep_symbols:
                    # Create raw node key: (kind, price_field, symbol)
                    field = raw_dep.price_field or ""
                    raw_key = ("raw", raw_dep.kind, field, dep_symbol)

                    # Add edge: indicator depends on raw
                    if raw_key not in graph[ind_key]:
                        graph[ind_key].append(raw_key)

                    # Ensure raw node exists in graph
                    if raw_key not in graph:
                        graph[raw_key] = []  # Raw nodes have no dependencies

            # Add indicator dependencies (recursive)
            for ind_dep in reqs.indicators:
                dep_symbols = ind_dep.symbols if ind_dep.symbols else [symbol]
                dep_hash = stable_params_hash(ind_dep.params)

                for dep_symbol in dep_symbols:
                    dep_key = ("indicator", ind_dep.name, dep_hash, dep_symbol)

                    # Add edge: indicator depends on upstream indicator
                    if dep_key not in graph[ind_key]:
                        graph[ind_key].append(dep_key)

                    # Recursively visit dependency
                    if dep_key not in visited:
                        visit_indicator(ind_dep.name, ind_dep.params, [dep_symbol])

    # Start DFS from target indicator
    visit_indicator(req.indicator_name, req.params, req.symbols)

    # 3. Topological sort using Kahn's algorithm
    in_degree: dict[tuple[str, ...], int] = {node: 0 for node in graph}

    # Calculate in-degrees
    for _node, deps in graph.items():
        for dep in deps:
            if dep in in_degree:
                in_degree[dep] += 1

    # Queue nodes with in-degree 0
    queue = [node for node in graph if in_degree[node] == 0]
    sorted_nodes: list[tuple[str, ...]] = []

    while queue:
        node = queue.pop(0)
        sorted_nodes.append(node)

        # Reduce in-degree of dependent nodes
        for dep in graph.get(node, []):
            if dep in in_degree:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

    # 4. Detect cycles
    if len(sorted_nodes) != len(graph):
        # Find nodes involved in cycle
        cycle_nodes = [node for node in graph if node not in sorted_nodes]
        raise CyclicDependencyError(
            f"Circular dependency detected involving: {cycle_nodes[:3]}..."
        )

    # Convert to PlanNode objects (dependencies first, reverse order)
    plan_nodes = []
    for key in reversed(sorted_nodes):  # Reverse so deps come first
        kind = key[0]  # "raw" or "indicator"
        node = PlanNode(kind=kind, key=key, params={})
        plan_nodes.append(node)

    return ExecutionPlan(nodes=plan_nodes)


def fetch_raw_slices(nodes: list[PlanNode]) -> dict[tuple[str, ...], Any]:
    """
    Fetch minimal raw series for all 'raw' nodes from data adapters.
    Apply WindowSpec at the adapter level to clip history.

    Returns:
      cache mapping: node.key -> series payload (engine-defined shape).
    """
    # Stub: wire to your data source in a later commit.
    return {}


def execute_plan(
    plan: ExecutionPlan,
    raw_cache: dict[tuple[str, ...], Any],
    request: ComputeRequest,
) -> TAOutput:
    """
    Execute the plan: iterate through nodes, assemble TAInput, call compute().

    For each indicator node:
    1. Gather its raw data dependencies from raw_cache
    2. Gather its indicator dependencies from indicator_cache
    3. Assemble TAInput
    4. Call indicator.compute(input, **params)
    5. Store results in indicator_cache
    6. Return TAOutput for the target indicator

    Args:
        plan: ExecutionPlan with topologically sorted nodes
        raw_cache: Cache of raw data (from fetch_raw_slices)
        request: Original ComputeRequest with indicator name, params, symbols

    Returns:
        TAOutput for the target indicator

    Raises:
        IndicatorNotFoundError: If indicator is not registered
        RuntimeError: If target indicator was not computed
    """
    # Cache for indicator outputs: (name, params_hash, symbol) -> value
    indicator_cache: dict[tuple[str, str, str], Any] = {}
    target_output: TAOutput | None = None

    # Process nodes in order (dependencies first)
    for node in plan.nodes:
        if node.kind == "raw":
            # Raw nodes are already in raw_cache, skip
            continue

        # Extract indicator info from node key: ("indicator", name, params_hash, symbol)
        _, ind_name, params_hash, symbol = node.key
        ind_cls = get_indicator(ind_name)
        if not ind_cls:
            raise IndicatorNotFoundError(f"Indicator '{ind_name}' not found")

        # Reconstruct params from hash (we'll need to track this differently)
        # For now, use request params if it's the target indicator
        if ind_name == request.indicator_name:
            ind_params = request.params
        else:
            # For dependencies, params are embedded in the node or requirements
            ind_params = node.params if node.params else {}

        # Gather raw data for all symbols in request
        candles_map: dict[str, list] = {}
        for sym in request.symbols:
            # Look for raw candle data: ("raw", "price", field, symbol)
            raw_key = ("raw", "price", "close", sym)  # Simplified: assume close
            if raw_key in raw_cache:
                candles_map[sym] = raw_cache[raw_key]

        # Gather indicator dependencies
        injected_indicators: dict[tuple[str, str, str], Any] = {}
        reqs = ind_cls.requirements()
        for ind_dep in reqs.indicators:
            dep_hash = stable_params_hash(ind_dep.params)
            for sym in request.symbols:
                dep_key = (ind_dep.name, dep_hash, sym)
                if dep_key in indicator_cache:
                    injected_indicators[dep_key] = indicator_cache[dep_key]

        # Assemble TAInput
        ta_input = TAInput(
            candles=candles_map,
            indicators=injected_indicators if injected_indicators else None,
            scope_symbols=request.symbols,
            eval_ts=request.eval_ts,
        )

        # Compute indicator
        output = ind_cls.compute(ta_input, **ind_params)

        # Store results in cache (per symbol)
        for sym, value in output.values.items():
            cache_key = (ind_name, params_hash, sym)
            indicator_cache[cache_key] = value

        # If this is the target indicator, save the output
        if ind_name == request.indicator_name:
            target_output = output

    if target_output is None:
        raise RuntimeError(
            f"Target indicator '{request.indicator_name}' was not computed. "
            f"This indicates a bug in the planner."
        )

    return target_output
