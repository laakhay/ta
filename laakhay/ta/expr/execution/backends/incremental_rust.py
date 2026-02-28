from __future__ import annotations

from typing import Any

import ta_py

from ....core.dataset import Dataset
from ....core.ohlcv import OHLCV
from ....core.series import Series
from ...ir.nodes import CallNode
from ...planner.manifest import build_rust_execution_payload
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
        if isinstance(dataset, Dataset) and self._can_execute_plan(plan):
            return self._evaluate_with_execute_plan(plan, dataset, symbol=symbol, timeframe=timeframe)

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
            if node.name not in {"rsi", "atr", "stochastic", "vwap"}:
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

    @staticmethod
    def _can_execute_plan(plan: PlanResult) -> bool:
        root = plan.graph.nodes[plan.graph.root_id].node
        return isinstance(root, CallNode) and root.name in {"rsi", "atr", "stochastic", "vwap"}

    def _evaluate_with_execute_plan(
        self,
        plan: PlanResult,
        dataset: Dataset,
        symbol: str | None,
        timeframe: str | None,
    ) -> dict[tuple[str, str, str], Series[Any]]:
        requests = self._build_requests(plan)
        if not requests:
            raise RuntimeError("execute_plan requires at least one rust-call request")

        selected_symbol, selected_timeframe, selected_source = self._resolve_partition(dataset, symbol, timeframe)
        payload = build_rust_execution_payload(
            plan,
            dataset_id=dataset.rust_dataset_id,
            symbol=selected_symbol,
            timeframe=selected_timeframe,
            source=selected_source,
            requests=requests,
        )
        outputs = ta_py.execute_plan_payload(payload)

        root_id = int(plan.graph.root_id)
        root_values = outputs.get(root_id)
        if root_values is None:
            raise RuntimeError(f"execute_plan did not return output for root node {root_id}")

        series_obj = dataset.series(selected_symbol, selected_timeframe, selected_source)
        if not isinstance(series_obj, OHLCV):
            raise RuntimeError(
                "execute_plan currently requires OHLCV partition in dataset for selected symbol/timeframe/source"
            )

        values = tuple(float(v) if v is not None else float("nan") for v in root_values)
        series = Series[Any](
            timestamps=series_obj.timestamps,
            values=values,
            symbol=selected_symbol,
            timeframe=selected_timeframe,
        )
        output_source = "default" if selected_source in {"ohlcv", "default"} else selected_source
        return {(selected_symbol, selected_timeframe, output_source): series}

    @staticmethod
    def _resolve_partition(dataset: Dataset, symbol: str | None, timeframe: str | None) -> tuple[str, str, str]:
        if symbol and timeframe:
            explicit = dataset.series(symbol, timeframe, "ohlcv")
            if isinstance(explicit, OHLCV):
                return symbol, timeframe, "ohlcv"

            fallback = dataset.series(symbol, timeframe, "default")
            if isinstance(fallback, OHLCV):
                return symbol, timeframe, "default"

            raise RuntimeError(f"dataset does not contain OHLCV source for symbol={symbol} timeframe={timeframe}")

        for key in dataset.keys:
            series_obj = dataset.series(key.symbol, key.timeframe, key.source)
            if isinstance(series_obj, OHLCV):
                return str(key.symbol), key.timeframe, key.source

        raise RuntimeError("dataset must contain at least one OHLCV partition for execute_plan")
