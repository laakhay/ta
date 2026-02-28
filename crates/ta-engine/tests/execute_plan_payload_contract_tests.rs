use std::collections::BTreeMap;

use ta_engine::contracts::{
    RustExecutionGraph, RustExecutionPartition, RustExecutionPayload, RustExecutionRequest,
};
use ta_engine::incremental::backend::{parse_execute_plan_payload, ExecutePlanError};
use ta_engine::incremental::contracts::IncrementalValue;

fn valid_payload() -> RustExecutionPayload {
    RustExecutionPayload {
        dataset_id: 1,
        partition: RustExecutionPartition {
            symbol: "BTCUSDT".to_string(),
            timeframe: "1m".to_string(),
            source: "ohlcv".to_string(),
        },
        graph: RustExecutionGraph {
            root_id: 10,
            node_order: vec![1, 2, 10],
            nodes: BTreeMap::from([
                (
                    1,
                    BTreeMap::from([("kind".to_string(), "source_ref".to_string())]),
                ),
                (
                    2,
                    BTreeMap::from([("kind".to_string(), "call".to_string())]),
                ),
                (
                    10,
                    BTreeMap::from([("kind".to_string(), "binary_op".to_string())]),
                ),
            ]),
            edges: BTreeMap::from([(10, vec![1, 2]), (2, vec![1])]),
        },
        requests: vec![RustExecutionRequest {
            node_id: 2,
            kernel_id: "rsi".to_string(),
            input_field: "close".to_string(),
            kwargs: BTreeMap::from([("period".to_string(), IncrementalValue::Number(14.0))]),
        }],
    }
}

#[test]
fn parse_execute_payload_accepts_valid_contract() {
    let payload = valid_payload();
    let parsed = parse_execute_plan_payload(&payload).expect("payload should parse");
    assert_eq!(parsed.dataset_id, 1);
    assert_eq!(parsed.partition_key.symbol, "BTCUSDT");
    assert_eq!(parsed.requests.len(), 1);
}

#[test]
fn parse_execute_payload_rejects_missing_root() {
    let mut payload = valid_payload();
    payload.graph.root_id = 999;
    let err = parse_execute_plan_payload(&payload).expect_err("payload should fail");
    assert!(matches!(err, ExecutePlanError::InvalidPayload(_)));
}

#[test]
fn parse_execute_payload_rejects_unknown_kernel() {
    let mut payload = valid_payload();
    payload.requests[0].kernel_id = "unknown_kernel".to_string();
    let err = parse_execute_plan_payload(&payload).expect_err("payload should fail");
    assert_eq!(
        err,
        ExecutePlanError::UnsupportedKernelId("unknown_kernel".to_string())
    );
}
