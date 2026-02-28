from typing import Any

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.series import Series
from laakhay.ta.expr.algebra.operators import Expression
from laakhay.ta.expr.execution.backends.base import ExecutionBackend
from laakhay.ta.expr.planner.evaluator import Evaluator
from laakhay.ta.expr.planner.types import PlanResult


class BatchBackend(ExecutionBackend):
    """Backend that executes the expression graph using batch vectorization.

    This backend delegates to the existing Evaluator under the hood
    to preserve exact batch execution semantics.
    """

    def __init__(self) -> None:
        self._evaluator = Evaluator()

    def evaluate(
        self,
        plan: PlanResult,
        dataset: Dataset | dict[str, Series[Any]] | Series[Any],
        symbol: str | None = None,
        timeframe: str | None = None,
        **options: Any,
    ) -> Series[Any] | dict[tuple[str, str, str], Series[Any]]:
        # Evaluator requires an Expression wrapper around the graph root
        expr = Expression(plan.graph.nodes[plan.graph.root_id].node)
        # Inject the pre-computed plan so it doesn't plan again
        expr._plan_cache = plan

        return self._evaluator.evaluate(
            expr=expr, data=dataset, return_all_outputs=options.get("return_all_outputs", False)
        )

    def initialize(
        self,
        plan: PlanResult,
        dataset: Dataset,
        **options: Any,
    ) -> None:
        """Batch backend is stateless, no initialization needed."""
        pass

    def step(
        self,
        plan: PlanResult,
        _update_event: Any,
        **options: Any,
    ) -> None:
        """Batch backend does not support incremental stepping."""
        raise NotImplementedError("BatchBackend does not support incremental step operations.")

    def replay(
        self,
        plan: PlanResult,
        _replay_spec: Any,
        **options: Any,
    ) -> None:
        """Batch backend does not support partial replay."""
        raise NotImplementedError("BatchBackend does not support replay operations.")

    def snapshot(
        self,
        plan: PlanResult,
        **options: Any,
    ) -> Any:
        # Snapshot in batch typically means "run evaluate again" or return nothing.
        raise NotImplementedError("BatchBackend does not store state snapshots.")

    def clear_cache(self) -> None:
        """Clear the internal evaluator cache."""
        self._evaluator._cache.clear()
