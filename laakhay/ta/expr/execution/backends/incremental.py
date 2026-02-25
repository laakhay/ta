from typing import Any

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.series import Series
from laakhay.ta.expr.execution.node_adapters import (
    eval_aggregate_step,
    eval_binary_step,
    eval_call_step,
    eval_filter_step,
    eval_literal_step,
    eval_source_ref_step,
    eval_time_shift_step,
    eval_unary_step,
)
from laakhay.ta.expr.execution.state.models import KernelState
from laakhay.ta.expr.execution.state.store import StateStore
from laakhay.ta.expr.ir.nodes import (
    AggregateNode,
    BinaryOpNode,
    CallNode,
    FilterNode,
    LiteralNode,
    SourceRefNode,
    TimeShiftNode,
    UnaryOpNode,
)
from laakhay.ta.expr.planner.types import PlanResult

from .base import ExecutionBackend


class IncrementalBackend(ExecutionBackend):
    """Backend that evaluates an expression graph tick-by-tick."""

    def __init__(self) -> None:
        self._state_store = StateStore()

    def evaluate(
        self,
        plan: PlanResult,
        dataset: Dataset | dict[str, Series[Any]] | Series[Any],
        symbol: str | None = None,
        timeframe: str | None = None,
        **options: Any,
    ) -> Series[Any] | dict[tuple[str, str, str], Series[Any]]:
        """Evaluate an expression graph.

        For the IncrementalBackend, this typically implies iterating over
        the points in the dataset one by one, simulating a stream.
        This provides a way to test the incremental loop sequentially over a batch.
        """
        if isinstance(dataset, Series):
            ds = Dataset()
            ds.add(dataset)
        elif isinstance(dataset, dict):
            ds = Dataset()
            for k, v in dataset.items():
                ds.add(v, source=k)
        else:
            ds = dataset

        if ds.is_empty:
            return (
                {}
                if symbol is None
                else Series[Any](timestamps=(), values=(), symbol=symbol or "", timeframe=timeframe or "")
            )

        # Build context sequentially and step
        # For simplicity in this engine refactoring phase, we assume all series
        # share the exact same timestamp alignment (typical for simple indicator tests).
        # In a real streaming engine, we'd interleave by timestamp.
        all_series = [s for _, s in ds]
        if not all_series:
            return {}

        timestamps = all_series[0].timestamps
        n_points = len(timestamps)

        # We need historical warmup. For this runner, we'll just start stepping from 0.
        self.initialize(plan, ds, symbol, timeframe, **options)

        out_values = []
        out_mask = []
        for i in range(n_points):
            # Construct synthetic tick
            tick = {}
            for k, s in ds:
                # If OHLCV:
                if hasattr(s, "to_series"):
                    try:
                        tick[f"{k.source}.close"] = s.to_series("close").values[i]
                        tick["close"] = s.to_series("close").values[i]
                        tick["high"] = s.to_series("high").values[i]
                        tick["low"] = s.to_series("low").values[i]
                        tick["open"] = s.to_series("open").values[i]
                        tick["volume"] = s.to_series("volume").values[i]
                    except Exception:
                        pass
                else:
                    # Add source.field
                    # Also add just field
                    tick[f"{k.source}.{k.source}"] = s.values[i]
                    tick[k.source] = s.values[i]

            val = self.step(plan, tick, symbol, timeframe, **options)

            out_values.append(val)
            out_mask.append(val is not None)

        ref_symbol = symbol or all_series[0].symbol
        ref_tf = timeframe or all_series[0].timeframe

        res = Series[Any](
            timestamps=timestamps,
            values=tuple(out_values),
            symbol=ref_symbol,
            timeframe=ref_tf,
            availability_mask=tuple(out_mask),
        )

        if symbol is not None and timeframe is not None:
            return res
        return {(ref_symbol, ref_tf, "default"): res}

    def initialize(
        self,
        plan: PlanResult,
        history: Dataset,
        symbol: str | None = None,
        timeframe: str | None = None,
        **options: Any,
    ) -> None:
        """Prime the initial state of the graph based on historical warmup data."""
        self._state_store.clear()

    def step(
        self,
        plan: PlanResult,
        tick: dict[str, Any],
        symbol: str | None = None,
        timeframe: str | None = None,
        **options: Any,
    ) -> dict[str, Any] | Any:
        """Process a single incoming tick and update the state store.

        Args:
            plan: The resolved IR graph plan.
            tick: A dictionary mapping source keys to their scalar Decimal values at time t.
                  E.g., {"close": Decimal("100.5")}

        Returns:
            The output value of the root node for this tick.
        """
        graph = plan.graph
        order = plan.node_order
        node_outputs: dict[int, Any] = {}

        for node_id in order:
            node = graph.nodes[node_id]
            n = node.node

            # Fetch upstream values
            children_vals = [node_outputs[child_id] for child_id in node.children]

            # Get persistent state for this node
            state_container = self._state_store.get_state(node_id)

            # Evaluate scalar output for the node at time t
            out_val = self._eval_node_step(n, children_vals, tick, state_container)

            # Save value for downstreams and persist state
            node_outputs[node_id] = out_val
            state_container.last_value = out_val
            state_container.ticks_processed += 1
            if out_val is not None:
                state_container.history.append(out_val)
                state_container.is_valid = True

            self._state_store.update_state(node_id, state_container)

        return node_outputs[graph.root_id]

    def _eval_node_step(self, node: Any, children_vals: list[Any], tick: dict[str, Any], state: KernelState) -> Any:
        """Evaluate a single IR node incrementally."""
        if isinstance(node, SourceRefNode):
            return eval_source_ref_step(node, tick)

        if isinstance(node, LiteralNode):
            return eval_literal_step(node)

        if isinstance(node, BinaryOpNode):
            return eval_binary_step(node, children_vals)

        if isinstance(node, UnaryOpNode):
            return eval_unary_step(node, children_vals[0] if children_vals else None)

        if isinstance(node, FilterNode):
            return eval_filter_step(node, children_vals)

        if isinstance(node, AggregateNode):
            return eval_aggregate_step(node, children_vals[0] if children_vals else None, state)

        if isinstance(node, TimeShiftNode):
            return eval_time_shift_step(node, children_vals[0] if children_vals else None, state)

        if isinstance(node, CallNode):
            return eval_call_step(node, children_vals, tick, state)

        return None

    def replay(
        self,
        plan: PlanResult,
        snapshot: Any,
        events: list[dict[str, Any]],
        symbol: str | None = None,
        timeframe: str | None = None,
        **options: Any,
    ) -> list[Any]:
        """Replay a sequence of events from a given snapshot.

        This restores the engine to a previous mathematical state and computes
        the forward path for the given events.
        """
        self._state_store.restore(snapshot)
        results = []
        for tick in events:
            val = self.step(plan, tick, symbol, timeframe, **options)
            results.append(val)
        return results

    def snapshot(self, plan: PlanResult, **options: Any) -> Any:
        return self._state_store.snapshot()

    def clear_cache(self) -> None:
        self._state_store.clear()
