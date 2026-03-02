use serde_json::json;
use ta_engine::metadata::indicator_catalog;
use ta_engine::{compute_indicator, ComputeIndicatorRequest, OhlcvInput};

fn sample_ohlcv() -> OhlcvInput {
    OhlcvInput {
        timestamps: (1..=64).collect(),
        open: (1..=64).map(|v| v as f64).collect(),
        high: (1..=64).map(|v| v as f64 + 1.0).collect(),
        low: (1..=64).map(|v| v as f64 - 1.0).collect(),
        close: (1..=64).map(|v| v as f64 + 0.5).collect(),
        volume: Some((1..=64).map(|v| 1000.0 + v as f64).collect()),
    }
}

#[test]
fn computes_alias_id_with_alias_param_and_resolves_canonical_id() {
    let req = ComputeIndicatorRequest {
        indicator_id: "mean".to_string(),
        params: json!({"lookback": 5}),
        ohlcv: sample_ohlcv(),
        instance_id: Some("inst-1".to_string()),
    };

    let out = compute_indicator(req).expect("mean alias should resolve to sma");
    assert_eq!(out.indicator_id, "sma");
    assert_eq!(out.outputs.len(), 1);
    assert_eq!(out.outputs[0].name, "result");
    assert_eq!(out.outputs[0].values.len(), 64);
    assert_eq!(out.instance_id.as_deref(), Some("inst-1"));
    assert_eq!(out.normalized_params["period"], json!(5));
}

#[test]
fn computes_macd_with_metadata_output_order() {
    let req = ComputeIndicatorRequest {
        indicator_id: "macd".to_string(),
        params: json!({"fast_period": 12, "slow_period": 26, "signal_period": 9}),
        ohlcv: sample_ohlcv(),
        instance_id: None,
    };

    let out = compute_indicator(req).expect("macd should compute");
    let names: Vec<&str> = out.outputs.iter().map(|s| s.name.as_str()).collect();
    assert_eq!(names, vec!["macd", "signal", "histogram"]);
}

#[test]
fn returns_structured_error_for_invalid_param() {
    let req = ComputeIndicatorRequest {
        indicator_id: "sma".to_string(),
        params: json!({"period": 0}),
        ohlcv: sample_ohlcv(),
        instance_id: None,
    };

    let err = compute_indicator(req).expect_err("period=0 should fail");
    assert_eq!(err.code, "invalid_param");
}

#[test]
fn computes_event_signal_series() {
    let req = ComputeIndicatorRequest {
        indicator_id: "cross".to_string(),
        params: json!({"a": "close", "b": "open"}),
        ohlcv: sample_ohlcv(),
        instance_id: None,
    };

    let out = compute_indicator(req).expect("cross should compute");
    assert_eq!(out.outputs.len(), 1);
    assert_eq!(out.outputs[0].name, "result");
    assert_eq!(out.outputs[0].values.len(), 64);
}

#[test]
fn computes_all_catalog_indicators_with_defaults() {
    for meta in indicator_catalog() {
        let req = ComputeIndicatorRequest {
            indicator_id: meta.id.to_string(),
            params: json!({}),
            ohlcv: sample_ohlcv(),
            instance_id: None,
        };
        let out = compute_indicator(req).unwrap_or_else(|err| {
            panic!("{} failed with {}: {}", meta.id, err.code, err.message);
        });
        assert_eq!(out.outputs.len(), meta.outputs.len(), "{}", meta.id);
        for (idx, output) in out.outputs.iter().enumerate() {
            assert_eq!(output.name, meta.outputs[idx].name, "{}", meta.id);
        }
    }
}
