use std::collections::BTreeMap;

use ta_engine::incremental::contracts::{
    IncrementalValue, NodeSnapshotState, RuntimeSnapshot, TickUpdate,
    INCREMENTAL_STATE_SCHEMA_VERSION,
};

#[test]
fn tick_update_constructor_stores_index_and_fields() {
    let mut fields = BTreeMap::new();
    fields.insert("close".to_string(), IncrementalValue::Number(101.5));

    let u = TickUpdate::new(7, fields.clone());
    assert_eq!(u.event_index, 7);
    assert_eq!(u.fields, fields);
}

#[test]
fn runtime_snapshot_empty_uses_current_schema() {
    let snap = RuntimeSnapshot::empty();
    assert_eq!(snap.schema_version, INCREMENTAL_STATE_SCHEMA_VERSION);
    assert_eq!(snap.last_event_index, 0);
    assert!(snap.nodes.is_empty());
}

#[test]
fn node_snapshot_state_is_stable_shape() {
    let mut blob = BTreeMap::new();
    blob.insert("count".to_string(), IncrementalValue::Number(3.0));

    let node = NodeSnapshotState {
        ticks_processed: 3,
        last_output: IncrementalValue::Number(42.0),
        state_blob: blob,
    };

    assert_eq!(node.ticks_processed, 3);
}
