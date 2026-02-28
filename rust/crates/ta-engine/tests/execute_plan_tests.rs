use std::collections::BTreeMap;

use ta_engine::dataset::{append_ohlcv, create_dataset, drop_dataset, DatasetPartitionKey};
use ta_engine::incremental::backend::{execute_plan, ExecutePlanError, KernelStepRequest};
use ta_engine::incremental::contracts::IncrementalValue;
use ta_engine::incremental::kernel_registry::KernelId;

fn key(symbol: &str, timeframe: &str, source: &str) -> DatasetPartitionKey {
    DatasetPartitionKey {
        symbol: symbol.to_string(),
        timeframe: timeframe.to_string(),
        source: source.to_string(),
    }
}

#[test]
fn execute_plan_runs_single_kernel_across_dataset_rows() {
    let dataset_id = create_dataset();
    append_ohlcv(
        dataset_id,
        key("BTCUSDT", "1m", "ohlcv"),
        &[1, 2, 3, 4, 5],
        &[10.0, 11.0, 12.0, 13.0, 14.0],
        &[11.0, 12.0, 13.0, 14.0, 15.0],
        &[9.0, 10.0, 11.0, 12.0, 13.0],
        &[10.5, 11.5, 12.5, 13.5, 14.5],
        &[100.0, 101.0, 102.0, 103.0, 104.0],
    )
    .expect("append should succeed");

    let request = KernelStepRequest {
        node_id: 1,
        kernel_id: KernelId::Rsi,
        input_field: "close".to_string(),
        kwargs: BTreeMap::from([("period".to_string(), IncrementalValue::Number(2.0))]),
    };

    let out = execute_plan(dataset_id, &key("BTCUSDT", "1m", "ohlcv"), &[request])
        .expect("execute plan should succeed");
    let values = out.get(&1).expect("node output should exist");
    assert_eq!(values.len(), 5);

    drop_dataset(dataset_id).expect("drop should succeed");
}

#[test]
fn execute_plan_errors_for_missing_partition() {
    let dataset_id = create_dataset();
    let err = execute_plan(dataset_id, &key("BTCUSDT", "1m", "ohlcv"), &[])
        .expect_err("missing partition should error");
    assert_eq!(
        err,
        ExecutePlanError::PartitionNotFound {
            symbol: "BTCUSDT".to_string(),
            timeframe: "1m".to_string(),
            data_source: "ohlcv".to_string(),
        }
    );
    drop_dataset(dataset_id).expect("drop should succeed");
}
