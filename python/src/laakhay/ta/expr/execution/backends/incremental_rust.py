from __future__ import annotations

import math
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
    ) -> Any:
        return_all_outputs = bool(options.get("return_all_outputs", False))
        if not isinstance(dataset, Dataset):
            raise RuntimeError("IncrementalRustBackend requires Dataset input")
        if not self._can_execute_plan(plan):
            raise RuntimeError("plan contains unsupported nodes for rust graph execution backend")
        return self._evaluate_with_execute_plan(
            plan,
            dataset,
            symbol=symbol,
            timeframe=timeframe,
            return_all_outputs=return_all_outputs,
        )

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
        allowed_calls = {
            "select",
            "sma",
            "mean",
            "rolling_mean",
            "rolling_median",
            "median",
            "ema",
            "rolling_ema",
            "wma",
            "rolling_wma",
            "rsi",
            "roc",
            "cmo",
            "atr",
            "bbands",
            "bb_upper",
            "bb_lower",
            "donchian",
            "keltner",
            "stochastic",
            "stoch_k",
            "stoch_d",
            "adx",
            "macd",
            "swing_high_at",
            "swing_low_at",
            "fib_level_down",
            "fib_level_up",
            "fib_down",
            "crossup",
            "crossdown",
            "cross",
            "rising",
            "falling",
            "rising_pct",
            "falling_pct",
            "in_channel",
            "out",
            "enter",
            "exit",
        }
        allowed_binary = {"gt", "gte", "lt", "lte", "eq", "neq", "and", "or", "add", "sub", "mul", "div", "mod", "pow"}
        for graph_node in plan.graph.nodes.values():
            node = graph_node.node
            if type(node).__name__ == "SourceRefNode":
                field = getattr(node, "field", None)
                if field is None:
                    return False
                if any(
                    getattr(node, attr, None) is not None
                    for attr in ("symbol", "exchange", "timeframe")
                ):
                    return False
                continue
            if type(node).__name__ == "LiteralNode":
                value = getattr(node, "value", None)
                if not isinstance(value, int | float | bool | str):
                    return False
                continue
            if type(node).__name__ == "CallNode":
                if not isinstance(node, CallNode) or node.name not in allowed_calls:
                    return False
                continue
            if type(node).__name__ == "BinaryOpNode":
                op = getattr(node, "operator", None)
                if op not in allowed_binary:
                    return False
                continue
            if type(node).__name__ == "UnaryOpNode":
                op = getattr(node, "operator", None)
                if op not in {"not", "neg", "pos"}:
                    return False
                continue
            if type(node).__name__ == "TimeShiftNode":
                op = getattr(node, "operation", None)
                if op not in {None, "change", "change_pct"}:
                    return False
                continue
            if type(node).__name__ == "FilterNode":
                continue
            if type(node).__name__ == "AggregateNode":
                op = getattr(node, "operation", None)
                if op not in {"count", "sum", "avg", "max", "min"}:
                    return False
                continue
            return False
        return True

    def _evaluate_with_execute_plan(
        self,
        plan: PlanResult,
        dataset: Dataset,
        symbol: str | None,
        timeframe: str | None,
        return_all_outputs: bool,
    ) -> Any:
        selected_symbol, selected_timeframe, selected_source = self._resolve_partition(
            plan,
            dataset,
            symbol,
            timeframe,
        )
        payload = build_rust_execution_payload(
            plan,
            dataset_id=dataset.rust_dataset_id,
            symbol=selected_symbol,
            timeframe=selected_timeframe,
            source=selected_source,
            requests=[],
        )
        outputs = ta_py.execute_plan_payload(payload)

        root_id = int(plan.graph.root_id)
        root_values = outputs.get(root_id)
        if root_values is None:
            raise RuntimeError(f"execute_plan did not return output for root node {root_id}")

        series_obj = dataset.series(selected_symbol, selected_timeframe, selected_source)
        if isinstance(series_obj, OHLCV):
            timestamps = series_obj.timestamps
        elif isinstance(series_obj, Series):
            timestamps = series_obj.timestamps
        else:
            raise RuntimeError("execute_plan could not resolve timestamps for selected partition")

        warmup = 0
        if plan.requirements.data_requirements:
            warmup = max(int(req.min_lookback) for req in plan.requirements.data_requirements) - 1
            warmup = max(warmup, 0)

        def _to_series(raw_values: list[Any]) -> Series[Any]:
            normalized_values: list[Any] = []
            for value in raw_values:
                if isinstance(value, bool):
                    normalized_values.append(value)
                    continue
                if isinstance(value, str):
                    normalized_values.append(value)
                    continue
                if value is None:
                    normalized_values.append(None)
                    continue
                number = float(value)
                normalized_values.append(None if math.isnan(number) else number)
            values = tuple(normalized_values)
            availability_mask = [v is not None for v in values]
            if warmup > 0:
                for i in range(min(warmup, len(availability_mask))):
                    availability_mask[i] = False
            return Series[Any](
                timestamps=timestamps,
                values=values,
                symbol=selected_symbol,
                timeframe=selected_timeframe,
                availability_mask=tuple(availability_mask),
            )

        series = _to_series(root_values)
        results = {(selected_symbol, selected_timeframe, "default"): series}
        if not return_all_outputs:
            return results
        node_outputs = {int(node_id): _to_series(node_values) for node_id, node_values in outputs.items()}
        return results, node_outputs

    @staticmethod
    def _resolve_partition(
        plan: PlanResult,
        dataset: Dataset,
        symbol: str | None,
        timeframe: str | None,
    ) -> tuple[str, str, str]:
        referenced_sources = {
            str(getattr(graph_node.node, "source", "")).strip()
            for graph_node in plan.graph.nodes.values()
            if type(graph_node.node).__name__ == "SourceRefNode" and getattr(graph_node.node, "source", None)
        }
        referenced_fields = {
            str(getattr(graph_node.node, "field", "")).strip()
            for graph_node in plan.graph.nodes.values()
            if type(graph_node.node).__name__ == "SourceRefNode" and getattr(graph_node.node, "field", None)
        }
        for graph_node in plan.graph.nodes.values():
            node = graph_node.node
            if not isinstance(node, CallNode) or node.name != "select":
                continue
            if not graph_node.children:
                continue
            first_child = plan.graph.nodes.get(graph_node.children[0])
            value = getattr(getattr(first_child, "node", None), "value", None)
            if isinstance(value, str) and value:
                referenced_fields.add(value)
        preferred_sources = [source for source in referenced_sources if source and source != "ohlcv"]
        preferred_source = preferred_sources[0] if len(preferred_sources) == 1 else None
        if preferred_source is None and len(referenced_fields) == 1:
            field_source = next(iter(referenced_fields))
            if any(key.source == field_source for key in dataset.keys):
                preferred_source = field_source
            elif not any(key.source == "ohlcv" for key in dataset.keys):
                raise RuntimeError(f"dataset does not contain required source field partition: {field_source}")

        if symbol and timeframe:
            if preferred_source:
                explicit = dataset.series(symbol, timeframe, preferred_source)
                if isinstance(explicit, OHLCV | Series):
                    return symbol, timeframe, preferred_source
            explicit = dataset.series(symbol, timeframe, "ohlcv")
            if isinstance(explicit, OHLCV | Series):
                return symbol, timeframe, "ohlcv"
            raise RuntimeError(f"dataset does not contain symbol={symbol} timeframe={timeframe}")

        for key in dataset.keys:
            if preferred_source and key.source != preferred_source:
                continue
            series_obj = dataset.series(key.symbol, key.timeframe, key.source)
            if isinstance(series_obj, OHLCV | Series):
                return str(key.symbol), key.timeframe, key.source

        if preferred_source:
            raise RuntimeError(f"dataset must contain at least one partition for source={preferred_source}")
        if referenced_fields:
            fields = ",".join(sorted(referenced_fields))
            raise RuntimeError(f"dataset does not contain required source field partitions: {fields}")
        raise RuntimeError("dataset must contain at least one partition for execute_plan")
