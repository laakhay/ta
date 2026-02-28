use ta_engine::dataset::{
    append_ohlcv, append_series, create_dataset, dataset_info, drop_dataset, DatasetPartitionKey,
    DatasetRegistryError,
};

fn key(symbol: &str, timeframe: &str, source: &str) -> DatasetPartitionKey {
    DatasetPartitionKey {
        symbol: symbol.to_string(),
        timeframe: timeframe.to_string(),
        source: source.to_string(),
    }
}

#[test]
fn append_ohlcv_accepts_valid_payload() {
    let id = create_dataset();
    let out = append_ohlcv(
        id,
        key("BTCUSDT", "1m", "ohlcv"),
        &[1, 2, 3],
        &[10.0, 11.0, 12.0],
        &[12.0, 13.0, 14.0],
        &[9.0, 10.0, 11.0],
        &[11.0, 12.0, 13.0],
        &[100.0, 200.0, 300.0],
    )
    .expect("append should succeed");
    assert_eq!(out, 3);

    let info = dataset_info(id).expect("dataset info should exist");
    assert_eq!(info.partition_count, 1);
    assert_eq!(info.ohlcv_row_count, 3);

    drop_dataset(id).expect("drop should succeed");
}

#[test]
fn append_rejects_length_mismatch() {
    let id = create_dataset();
    let out = append_ohlcv(
        id,
        key("BTCUSDT", "1m", "ohlcv"),
        &[1, 2, 3],
        &[10.0, 11.0],
        &[12.0, 13.0, 14.0],
        &[9.0, 10.0, 11.0],
        &[11.0, 12.0, 13.0],
        &[100.0, 200.0, 300.0],
    );
    assert_eq!(
        out,
        Err(DatasetRegistryError::LengthMismatch {
            field: "open",
            expected: 3,
            got: 2
        })
    );

    drop_dataset(id).expect("drop should succeed");
}

#[test]
fn append_rejects_non_monotonic_timestamps() {
    let id = create_dataset();
    let out = append_series(
        id,
        key("BTCUSDT", "1m", "trades"),
        "price".to_string(),
        &[1, 3, 2],
        &[101.0, 102.0, 103.0],
    );
    assert_eq!(
        out,
        Err(DatasetRegistryError::NonMonotonicTimestamps {
            field: "timestamps"
        })
    );

    drop_dataset(id).expect("drop should succeed");
}

#[test]
fn append_supports_multi_partition_and_series() {
    let id = create_dataset();

    append_ohlcv(
        id,
        key("BTCUSDT", "1m", "ohlcv"),
        &[1, 2],
        &[10.0, 11.0],
        &[12.0, 13.0],
        &[9.0, 10.0],
        &[11.0, 12.0],
        &[100.0, 200.0],
    )
    .expect("ohlcv append should succeed");

    append_series(
        id,
        key("ETHUSDT", "5m", "trades"),
        "price".to_string(),
        &[1, 2, 3],
        &[201.0, 202.0, 203.0],
    )
    .expect("series append should succeed");

    let info = dataset_info(id).expect("dataset info should exist");
    assert_eq!(info.partition_count, 2);
    assert_eq!(info.ohlcv_row_count, 2);
    assert_eq!(info.series_count, 1);
    assert_eq!(info.series_row_count, 3);

    drop_dataset(id).expect("drop should succeed");
}
