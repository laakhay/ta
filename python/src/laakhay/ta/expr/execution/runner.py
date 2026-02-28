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
    exec_backend = backend or resolve_backend(mode)
    return exec_backend.evaluate(plan, data, **options)
