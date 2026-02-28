from typing import Any, Protocol

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.series import Series
from laakhay.ta.expr.planner.types import PlanResult


class ExecutionBackend(Protocol):
    """Protocol defining the interface for expression execution backends."""

    def evaluate(
        self,
        plan: PlanResult,
        dataset: Dataset | dict[str, Series[Any]] | Series[Any],
        symbol: str | None = None,
        timeframe: str | None = None,
        **options: Any,
    ) -> Series[Any] | dict[tuple[str, str, str], Series[Any]]:
        """Evaluate an expression graph against a dataset snapshot."""
        ...

    def initialize(
        self,
        plan: PlanResult,
        dataset: Dataset,
        **options: Any,
    ) -> None:
        """Initialize the backend state against historical dataset."""
        ...

    def step(
        self,
        plan: PlanResult,
        _update_event: Any,
        **options: Any,
    ) -> None:
        """Process an incremental update event."""
        ...

    def replay(
        self,
        plan: PlanResult,
        _replay_spec: Any,
        **options: Any,
    ) -> None:
        """Replay a specific range of historical data."""
        ...

    def snapshot(
        self,
        plan: PlanResult,
        **options: Any,
    ) -> Any:
        """Get the current snapshot of output series/state."""
        ...

    def clear_cache(self) -> None:
        """Clear any internal caches or state."""
        ...
