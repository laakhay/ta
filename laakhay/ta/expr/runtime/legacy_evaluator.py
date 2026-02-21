"""Legacy runtime evaluator compatibility wrapper.

Canonical evaluator logic lives in ``laakhay.ta.expr.planner.evaluator.Evaluator``.
This module preserves the historical RuntimeEvaluator API surface while delegating
execution to the canonical planner evaluator core.
"""

from __future__ import annotations

from typing import Any

from ...core import Series
from ...core.dataset import Dataset
from ...exceptions import EvaluationError
from ..execution.context_builder import build_evaluation_context, collect_required_field_names
from ..execution.time_shift import parse_shift_periods
from ..planner.evaluator import Evaluator
from ..planner.types import PlanResult


class RuntimeEvaluator(Evaluator):
    """Compatibility wrapper over the canonical planner Evaluator."""

    def evaluate(
        self,
        plan: PlanResult,
        dataset: Dataset,
        symbol: str | None = None,
        timeframe: str | None = None,
    ) -> Series[Any] | dict[tuple[str, str, str], Series[Any]]:
        if dataset.is_empty:
            return (
                {}
                if symbol is None
                else Series[Any](timestamps=(), values=(), symbol=symbol or "", timeframe=timeframe or "")
            )

        if symbol is not None and timeframe is not None:
            required_fields = collect_required_field_names(plan.requirements)
            context = build_evaluation_context(dataset, symbol, timeframe, required_fields)
            return self._evaluate_graph(plan, context, symbol, timeframe)

        # Delegate dataset fan-out path to canonical evaluator core.
        return self._evaluate_dataset(expr=None, plan=plan, dataset=dataset, return_all_outputs=False)

    def clear_cache(self) -> None:
        self._cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        return {
            "cache_size": len(self._cache),
            "cache_keys": list(self._cache.keys())[:10],
        }

    def _parse_shift_periods(self, shift: str) -> int:
        try:
            return parse_shift_periods(shift)
        except ValueError as exc:
            raise EvaluationError(
                f"Invalid shift format: {shift}",
                node_type="TimeShiftExpression",
                context={"shift": shift},
            ) from exc
