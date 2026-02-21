from typing import Any

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.series import Series
from laakhay.ta.expr.execution.node_adapters import eval_binary_step, eval_literal_step, eval_source_ref_step
from laakhay.ta.expr.ir.nodes import BinaryOpNode, CallNode, LiteralNode, SourceRefNode
from laakhay.ta.expr.planner.types import PlanResult
from laakhay.ta.expr.runtime.state.models import KernelState
from laakhay.ta.expr.runtime.state.store import StateStore
from laakhay.ta.primitives.adapters.registry_binding import coerce_incremental_input, resolve_kernel_for_indicator

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
        out_timestamps = []
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

            # If val is None, it means the graph is still warming up (e.g. SMA needs 14 periods)
            if val is not None:
                out_values.append(val)
                out_timestamps.append(timestamps[i])

        ref_symbol = symbol or all_series[0].symbol
        ref_tf = timeframe or all_series[0].timeframe

        from laakhay.ta.core.types import Price

        final_vals = tuple(Price(v) for v in out_values)

        res = Series[Any](
            timestamps=tuple(out_timestamps),
            values=final_vals,
            symbol=ref_symbol,
            timeframe=ref_tf,
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

        from laakhay.ta.registry.registry import get_global_registry

        if isinstance(node, CallNode):
            # This is an indicator call (e.g. SMA) that uses the Kernel protocol.
            registry = get_global_registry()
            # If the user registered it via the @register decorator,
            # we need a way to extract the underlying Kernel instance.
            name = node.name

            # Map kwarg evaluated values
            kwargs = {}
            handle = registry.get(name)
            if handle:
                import inspect

                sig = inspect.signature(handle.func)
                # First child is always the input series (ctx / source), subsequent children are args
                # kwargs are appended at the end

                # filter out 'ctx' from signature if present
                param_names = [p.name for p in sig.parameters.values() if p.name != "ctx"]

                # 1. Map positional children to parameter names
                arg_vals = children_vals[1 : 1 + len(node.args)] if len(children_vals) > 1 else []
                for i, val in enumerate(arg_vals):
                    if i < len(param_names):
                        kwargs[param_names[i]] = val

                # 2. Map explict kwargs
                kwarg_vals = children_vals[1 + len(node.args) :]
                for k, val in zip(sorted(node.kwargs.keys()), kwarg_vals, strict=False):
                    kwargs[k] = val

                # 3. Fill in missing defaults
                for p in sig.parameters.values():
                    if p.name != "ctx" and p.name not in kwargs and p.default is not inspect.Parameter.empty:
                        kwargs[p.name] = p.default
            else:
                # Fallback if not in registry
                kwarg_vals = children_vals[1 + len(node.args) :]
                for k, val in zip(sorted(node.kwargs.keys()), kwarg_vals, strict=False):
                    kwargs[k] = val

            input_val = children_vals[0] if children_vals else None
            if input_val is None:
                return None

            # Dynamically instantiate the kernel if it hasn't been yet
            if state.algorithm_state is None:
                kernel = resolve_kernel_for_indicator(name)
                if kernel is None:
                    # Fallback (not a pure kernel)
                    return None
                # Initialize state with empty history
                state.algorithm_state = kernel.initialize([], **kwargs)
                state._kernel_instance = kernel

            # Execute one step
            kernel = state._kernel_instance
            input_val = coerce_incremental_input(name, input_val, tick, state.algorithm_state)

            new_alg_state, out_val = kernel.step(state.algorithm_state, input_val, **kwargs)
            state.algorithm_state = new_alg_state
            return out_val

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
