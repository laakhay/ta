from decimal import Decimal

import pytest

from laakhay.ta.expr.execution.state.models import STATE_SCHEMA_VERSION, KernelState, StateSnapshot
from laakhay.ta.expr.execution.state.store import StateStore


def test_state_store_snapshot_roundtrip_versioned() -> None:
    store = StateStore()
    state = store.get_state(1)
    state.last_value = Decimal("2")
    store.update_state(1, state)

    snap = store.snapshot()
    assert snap.schema_version == STATE_SCHEMA_VERSION
    assert 1 in snap.states

    new_store = StateStore()
    new_store.restore(snap)
    restored = new_store.get_state(1)
    assert restored.last_value == Decimal("2")


def test_state_store_restore_rejects_wrong_schema() -> None:
    store = StateStore()
    bad = StateSnapshot(schema_version=999, states={})
    with pytest.raises(ValueError, match="Incompatible snapshot schema"):
        store.restore(bad)


def test_state_store_restore_supports_raw_dict_snapshot() -> None:
    store = StateStore()
    legacy = {2: KernelState(last_value=Decimal("3"))}
    store.restore(legacy)
    assert store.get_state(2).last_value == Decimal("3")
