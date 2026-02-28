use ta_engine::dataset_ops::{downsample, sync_timeframe, upsample_ffill, DatasetOpsError};

#[test]
fn downsample_last_mean_sum() {
    let ts = vec![1, 2, 3, 4, 5];
    let values = vec![10.0, 20.0, 30.0, 40.0, 50.0];

    let (last_ts, last_vals) = downsample(&ts, &values, 2, "last").expect("downsample last should work");
    assert_eq!(last_ts, vec![2, 4, 5]);
    assert_eq!(last_vals, vec![20.0, 40.0, 50.0]);

    let (mean_ts, mean_vals) = downsample(&ts, &values, 2, "mean").expect("downsample mean should work");
    assert_eq!(mean_ts, vec![2, 4, 5]);
    assert_eq!(mean_vals, vec![15.0, 35.0, 50.0]);

    let (sum_ts, sum_vals) = downsample(&ts, &values, 2, "sum").expect("downsample sum should work");
    assert_eq!(sum_ts, vec![2, 4, 5]);
    assert_eq!(sum_vals, vec![30.0, 70.0, 50.0]);
}

#[test]
fn downsample_rejects_invalid_agg() {
    let err = downsample(&[1, 2], &[10.0, 20.0], 2, "median").expect_err("invalid agg should error");
    assert_eq!(err, DatasetOpsError::UnsupportedAggregation("median".to_string()));
}

#[test]
fn upsample_ffill_expands_between_points() {
    let (ts, vals) = upsample_ffill(&[1, 3, 5], &[10.0, 20.0, 30.0], 3).expect("upsample should work");
    assert_eq!(ts, vec![1, 1, 1, 3, 3, 3, 5]);
    assert_eq!(vals, vec![10.0, 10.0, 10.0, 20.0, 20.0, 20.0, 30.0]);
}

#[test]
fn sync_timeframe_ffill_and_linear() {
    let source_ts = vec![10, 20, 30];
    let source_vals = vec![1.0, 3.0, 5.0];
    let ref_ts = vec![5, 10, 15, 20, 25, 35];

    let ffill = sync_timeframe(&source_ts, &source_vals, &ref_ts, "ffill").expect("ffill should work");
    assert_eq!(ffill, vec![1.0, 1.0, 1.0, 3.0, 3.0, 5.0]);

    let linear = sync_timeframe(&source_ts, &source_vals, &ref_ts, "linear").expect("linear should work");
    assert_eq!(linear, vec![1.0, 1.0, 2.0, 3.0, 4.0, 5.0]);
}
