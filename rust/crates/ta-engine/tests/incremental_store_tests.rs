use std::collections::BTreeMap;

use ta_engine::incremental::contracts::{IncrementalValue, RuntimeSnapshot};
use ta_engine::incremental::state::NodeRuntimeState;
use ta_engine::incremental::store::RuntimeStateStore;

#[test]
fn initialize_clears_existing_state() {
    let mut store = RuntimeStateStore::default();
    store.upsert_node(NodeRuntimeState {
        node_id: 1,
        ticks_processed: 2,
        last_output: IncrementalValue::Number(5.0),
        state_blob: BTreeMap::new(),
    });

    store.initialize();
    assert!(store.get_node(1).is_none());
}

#[test]
fn snapshot_restore_roundtrip_preserves_node_payload() {
    let mut store = RuntimeStateStore::default();
    let mut blob = BTreeMap::new();
    blob.insert("acc".to_string(), IncrementalValue::Number(9.0));
    store.set_last_event_index(17);
    store.upsert_node(NodeRuntimeState {
        node_id: 2,
        ticks_processed: 4,
        last_output: IncrementalValue::Bool(true),
        state_blob: blob,
    });

    let snap = store.snapshot();

    let mut restored = RuntimeStateStore::default();
    restored
        .restore(snap)
        .expect("snapshot with same schema should restore");

    let node = restored
        .get_node(2)
        .expect("node should exist after restore");
    assert_eq!(node.ticks_processed, 4);
    assert_eq!(node.last_output, IncrementalValue::Bool(true));
}

#[test]
fn restore_rejects_unknown_schema() {
    let mut store = RuntimeStateStore::default();
    let snapshot = RuntimeSnapshot {
        schema_version: 999,
        last_event_index: 0,
        nodes: BTreeMap::new(),
    };

    assert!(store.restore(snapshot).is_err());
}
