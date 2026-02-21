"""State lifecycle store for canonical execution namespace."""

from __future__ import annotations

from .models import STATE_SCHEMA_VERSION, KernelState, StateSnapshot


class StateStore:
    """Manages lifecycle and retrieval of node states during step execution."""

    def __init__(self) -> None:
        self._states: dict[int, KernelState] = {}

    def get_state(self, node_id: int) -> KernelState:
        if node_id not in self._states:
            self._states[node_id] = KernelState()
        return self._states[node_id]

    def update_state(self, node_id: int, state: KernelState) -> None:
        self._states[node_id] = state

    def clear(self) -> None:
        self._states.clear()

    def snapshot(self) -> StateSnapshot:
        import copy

        return StateSnapshot(schema_version=STATE_SCHEMA_VERSION, states=copy.deepcopy(self._states))

    def restore(self, snapshot: StateSnapshot | dict[int, KernelState]) -> None:
        import copy

        if isinstance(snapshot, StateSnapshot):
            if snapshot.schema_version != STATE_SCHEMA_VERSION:
                raise ValueError(
                    f"Incompatible snapshot schema {snapshot.schema_version}; expected {STATE_SCHEMA_VERSION}"
                )
            self._states = copy.deepcopy(snapshot.states)
            return
        # Backward compatibility for old raw dict snapshots.
        self._states = copy.deepcopy(snapshot)
