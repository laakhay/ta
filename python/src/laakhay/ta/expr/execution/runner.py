"""Single entrypoint for evaluating a planned expression."""

from __future__ import annotations

from typing import Any

from ...core.dataset import Dataset
from ...core.series import Series
from ..planner.types import PlanResult
from .backend import resolve_backend


def evaluate_plan(
    plan: PlanResult,
    data: Dataset | dict[str, Series[Any]] | Series[Any],
    *,
    backend: Any | None = None,
    mode: str | None = None,
    **options: Any,
) -> Any:
    """Evaluate a plan using the selected backend.

    - If `backend` is provided, it is used directly (useful for stateful stream loops).
    - Otherwise, backend is resolved from `mode` / environment.
    """
    if backend is not None:
        return backend.evaluate(plan, data, **options)

    class _PlannedExpr:
        def __init__(self, planned: PlanResult) -> None:
            self._plan = planned

        def _ensure_plan(self) -> PlanResult:
            return self._plan

    if not isinstance(data, Dataset):
        from ..planner.evaluator import Evaluator

        return Evaluator().evaluate(
            _PlannedExpr(plan),
            data,
            return_all_outputs=bool(options.get("return_all_outputs", False)),
        )

    if data.is_empty:
        from ..planner.evaluator import Evaluator

        return Evaluator().evaluate(
            _PlannedExpr(plan),
            data,
            return_all_outputs=bool(options.get("return_all_outputs", False)),
        )

    exec_backend = resolve_backend(mode)
    try:
        return exec_backend.evaluate(plan, data, **options)
    except RuntimeError:
        from ..planner.evaluator import Evaluator

        return Evaluator().evaluate(
            _PlannedExpr(plan),
            data,
            return_all_outputs=bool(options.get("return_all_outputs", False)),
        )
