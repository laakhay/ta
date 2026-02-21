"""State lifecycle store for the incremental backend."""

from __future__ import annotations

from .models import KernelState


class StateStore:
    """Manages the lifecycle and retrieval of all node states during incremental execution.

    In a DAG expression graph, each node requires its own unique state representation
    that must persist across ticks.
    """

    def __init__(self) -> None:
        # Map of node ID to its current KernelState
        self._states: dict[int, KernelState] = {}

    def get_state(self, node_id: int) -> KernelState:
        """Retrieve the state for a specific node, initializing if necessary."""
        if node_id not in self._states:
            self._states[node_id] = KernelState()
        return self._states[node_id]

    def update_state(self, node_id: int, state: KernelState) -> None:
        """Update the stored state instance for a node."""
        self._states[node_id] = state

    def clear(self) -> None:
        """Clear all states. Useful for resetting the engine."""
        self._states.clear()

    def snapshot(self) -> dict[int, KernelState]:
        """Produce a snapshot of the current state, potentially for replay/recovery."""
        import copy

        return copy.deepcopy(self._states)

    def restore(self, snapshot: dict[int, KernelState]) -> None:
        """Restore the engine's state from a prior snapshot."""
        import copy

        self._states = copy.deepcopy(snapshot)
