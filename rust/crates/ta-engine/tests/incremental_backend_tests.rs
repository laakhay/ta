use std::collections::BTreeMap;

use ta_engine::incremental::backend::{IncrementalBackend, KernelStepRequest};
use ta_engine::incremental::contracts::IncrementalValue;
use ta_engine::incremental::kernel_registry::KernelId;

#[test]
fn backend_step_snapshot_restore_replay_is_deterministic_for_rsi() {
    let requests = vec![KernelStepRequest {
        node_id: 1,
        kernel_id: KernelId::Rsi,
        input_field: "close".to_string(),
        kwargs: BTreeMap::from([("period".to_string(), IncrementalValue::Number(2.0))]),
    }];

    let events = vec![
        BTreeMap::from([("close".to_string(), IncrementalValue::Number(10.0))]),
        BTreeMap::from([("close".to_string(), IncrementalValue::Number(11.0))]),
        BTreeMap::from([("close".to_string(), IncrementalValue::Number(12.0))]),
        BTreeMap::from([("close".to_string(), IncrementalValue::Number(11.0))]),
    ];

    let mut backend = IncrementalBackend::default();
    backend.initialize();

    let _ = backend.step(1, &requests, &events[0]);
    let _ = backend.step(2, &requests, &events[1]);

    let snap = backend.snapshot();

    let cont_a = backend.replay(&requests, &events[2..]);

    let mut backend_b = IncrementalBackend::default();
    backend_b.initialize();
    backend_b
        .restore(snap)
        .expect("valid snapshot should restore");
    let cont_b = backend_b.replay(&requests, &events[2..]);

    assert_eq!(cont_a, cont_b);
}
