from __future__ import annotations

from typing import Any

import ta_py

from ....core.dataset import Dataset
from ....core.series import Series
from ...ir.nodes import CallNode
from ...planner.types import PlanResult
from .base import ExecutionBackend


class IncrementalRustBackend(ExecutionBackend):
    """Rust-backed incremental backend bridge.

    This backend intentionally handles incremental call-node kernels backed by
    Rust lifecycle bindings first. Non-call graph semantics stay in the Python
    incremental backend until parity migration is complete.
    """

    def __init__(self) -> None:
        self._backend_id = ta_py.incremental_initialize()
        self._requests: list[dict[str, Any]] = []

    def evaluate(
        self,
        plan: PlanResult,
        dataset: Dataset | dict[str, Series[Any]] | Series[Any],
        symbol: str | None = None,
        timeframe: str | None = None,
        **options: Any,
    ) -> Series[Any] | dict[tuple[str, str, str], Series[Any]]:
        # Full one-shot evaluate still routes through batch execution while
        # incremental lifecycle operations are handled by Rust.
        from .batch import BatchBackend

        return BatchBackend().evaluate(plan, dataset, symbol, timeframe, **options)

    def initialize(
        self,
        plan: PlanResult,
        history: Dataset,
        symbol: str | None = None,
        timeframe: str | None = None,
        **options: Any,
    ) -> None:
        self._requests = self._build_requests(plan)

    def step(
        self,
        plan: PlanResult,
        tick: dict[str, Any],
        symbol: str | None = None,
        timeframe: str | None = None,
        **options: Any,
    ) -> dict[str, Any] | Any:
        event_index = int(options.get("event_index", 0))
        out = ta_py.incremental_step(self._backend_id, self._requests, tick, event_index)
        root_id = plan.graph.root_id
        return out.get(root_id)

    def replay(
        self,
        plan: PlanResult,
        snapshot: Any,
        events: list[dict[str, Any]],
        symbol: str | None = None,
        timeframe: str | None = None,
        **options: Any,
    ) -> list[Any]:
        rows = ta_py.incremental_replay(self._backend_id, snapshot, self._requests, events)
        root_id = plan.graph.root_id
        return [row.get(root_id) for row in rows]

    def snapshot(self, plan: PlanResult, **options: Any) -> Any:
        return ta_py.incremental_snapshot(self._backend_id)

    def clear_cache(self) -> None:
        self._backend_id = ta_py.incremental_initialize()
        self._requests = []

    @staticmethod
    def _build_requests(plan: PlanResult) -> list[dict[str, Any]]:
        requests: list[dict[str, Any]] = []
        for node_id in plan.node_order:
            node = plan.graph.nodes[node_id].node
            if not isinstance(node, CallNode):
                continue
            if node.name not in {"rsi", "atr", "stochastic"}:
                continue

            kwargs: dict[str, Any] = {}
            for key, val in node.kwargs.items():
                if hasattr(val, "value"):
                    kwargs[key] = float(val.value)

            requests.append(
                {
                    "node_id": int(node_id),
                    "kernel_id": node.name,
                    "input_field": "close",
                    "kwargs": kwargs,
                }
            )
        return requests
