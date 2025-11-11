"""Evaluator using planned graphs for caching and dataset fan-out."""

from __future__ import annotations

from typing import Any

from ..core import Series
from ..core.dataset import Dataset
from ..core.series import align_series
from ..expressions.models import SCALAR_SYMBOL, BinaryOp, Literal, OperatorType, UnaryOp
from .types import PlanResult, SignalRequirements


class Evaluator:
    def __init__(self) -> None:
        # Per-node cache: (graph_hash, node_id, alignment, symbol, timeframe) -> output
        self._cache: dict[tuple, Any] = {}

    def evaluate(self, expr, data: Series[Any] | Dataset) -> Series[Any] | dict[tuple[str, str, str], Series[Any]]:
        plan = expr._ensure_plan()
        if isinstance(data, Series):
            context: dict[str, Series[Any]] = {"close": data}
            # Node-level caching is not performed for Series input
            return self._evaluate_graph(plan, context)
        if isinstance(data, Dataset):
            return self._evaluate_dataset(expr, plan, data)
        raise TypeError("Evaluator expects Series or Dataset")

    def _evaluate_dataset(self, expr, plan: PlanResult, dataset: Dataset) -> dict[tuple[str, str, str], Series[Any]]:
        if dataset.is_empty:
            return {}

        required_fields = _collect_required_field_names(plan.requirements)
        results: dict[tuple[str, str, str], Series[Any]] = {}
        unique_keys = {(key.symbol, key.timeframe) for key in dataset.keys}
        for symbol, timeframe in unique_keys:
            alignment_key = plan.alignment.cache_key()
            node_cache_key = (
                plan.graph_hash,
                plan.graph.root_id,
                alignment_key,
                symbol,
                timeframe,
            )
            if node_cache_key in self._cache:
                # Only retrieve the root node if all subnodes already cached
                results[(symbol, timeframe, "default")] = self._cache[node_cache_key]
                continue
            context = dataset.build_context(symbol, timeframe, required_fields)
            context_dict = {name: getattr(context, name) for name in context.available_series}
            output = self._evaluate_graph(plan, context_dict, symbol, timeframe)
            results[(symbol, timeframe, "default")] = output
        return results

    def _evaluate_graph(
        self,
        plan: PlanResult,
        context: dict[str, Any],
        symbol: str = None,
        timeframe: str = None,
    ) -> Any:
        graph = plan.graph
        order = plan.node_order
        node_outputs: dict[int, Any] = {}
        alignment = plan.alignment
        alignment_args = dict(
            how=alignment.how,
            fill=alignment.fill,
            left_fill_value=alignment.left_fill_value,
            right_fill_value=alignment.right_fill_value,
        )
        for node_id in order:
            node = graph.nodes[node_id]
            children_outputs = [node_outputs[child_id] for child_id in node.children]
            cache_key = (
                (plan.graph_hash, node_id, alignment.cache_key(), symbol, timeframe)
                if symbol is not None and timeframe is not None
                else None
            )

            if cache_key is not None and cache_key in self._cache:
                out = self._cache[cache_key]
            else:
                out = self._eval_node(node, children_outputs, context, alignment_args)
                if cache_key is not None:
                    self._cache[cache_key] = out
            node_outputs[node_id] = out
        return node_outputs[graph.root_id]

    def _eval_node(self, node, children_outputs, context, alignment_args):
        n = node.node
        # BinaryOp central alignment
        if isinstance(n, BinaryOp):
            arithmetic_ops = {
                OperatorType.ADD,
                OperatorType.SUB,
                OperatorType.MUL,
                OperatorType.DIV,
                OperatorType.MOD,
                OperatorType.POW,
            }
            comparison_ops = {
                OperatorType.EQ,
                OperatorType.NE,
                OperatorType.LT,
                OperatorType.LE,
                OperatorType.GT,
                OperatorType.GE,
            }
            # If operator is a Series operation, align both children before passing to op logic
            if n.operator in arithmetic_ops | comparison_ops:
                left, right = children_outputs[0], children_outputs[1]
                if isinstance(left, Series) and isinstance(right, Series):
                    left_is_scalar = left.symbol == SCALAR_SYMBOL
                    right_is_scalar = right.symbol == SCALAR_SYMBOL
                    if not (left_is_scalar or right_is_scalar):
                        left, right = align_series(
                            left,
                            right,
                            **alignment_args,
                            symbol=left.symbol,
                            timeframe=left.timeframe,
                        )
                return n.evaluate_aligned(left, right)
            # Otherwise, fallback to default logic (e.g. logical)
            return n.evaluate(context)
        elif isinstance(n, UnaryOp):
            return n.evaluate(context)
        elif isinstance(n, Literal):
            result = n.evaluate(context)
            # If result is a scalar Series, extract the scalar value for test compatibility
            if isinstance(result, Series) and result.symbol == SCALAR_SYMBOL and len(result) == 1:
                return result.values[0]
            return result
        elif hasattr(n, "__class__") and n.__class__.__name__ == "IndicatorNode":
            # For now, simply invoke .run(context) if present (stub; to be improved)
            return n.run(context)
        else:
            raise NotImplementedError(f"Unsupported node type: {type(n)}")


def _collect_required_field_names(requirements: SignalRequirements) -> list[str]:
    names = {field.name for field in requirements.fields if field.name}
    if not names:
        names = {"close"}
    return sorted(names)
