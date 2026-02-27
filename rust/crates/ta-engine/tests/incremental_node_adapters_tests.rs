use std::collections::BTreeMap;

use ta_engine::incremental::contracts::IncrementalValue;
use ta_engine::incremental::node_adapters::{
    eval_aggregate_step, eval_binary_step, eval_filter_step, eval_literal_step,
    eval_source_ref_step, eval_time_shift_step, eval_unary_step, AggregateState, SourceRef,
    TimeShiftState,
};

#[test]
fn source_ref_prefers_source_field_then_field() {
    let node = SourceRef {
        source: "ohlcv".to_string(),
        field: "close".to_string(),
    };
    let mut tick = BTreeMap::new();
    tick.insert("close".to_string(), IncrementalValue::Number(99.0));
    tick.insert("ohlcv.close".to_string(), IncrementalValue::Number(100.0));
    assert_eq!(
        eval_source_ref_step(&node, &tick),
        IncrementalValue::Number(100.0)
    );
}

#[test]
fn literal_unary_binary_filter_behave() {
    assert_eq!(
        eval_literal_step(&IncrementalValue::Number(7.0)),
        IncrementalValue::Number(7.0)
    );
    assert_eq!(
        eval_binary_step(
            "add",
            &IncrementalValue::Number(2.0),
            &IncrementalValue::Number(3.0)
        ),
        IncrementalValue::Number(5.0)
    );
    assert_eq!(
        eval_unary_step("neg", &IncrementalValue::Number(2.0)),
        IncrementalValue::Number(-2.0)
    );
    assert_eq!(
        eval_filter_step(
            &IncrementalValue::Number(5.0),
            &IncrementalValue::Bool(false)
        ),
        IncrementalValue::Null
    );
}

#[test]
fn aggregate_and_time_shift_paths_work() {
    let mut agg = AggregateState::default();
    assert_eq!(
        eval_aggregate_step("sum", &IncrementalValue::Number(2.0), &mut agg),
        IncrementalValue::Number(2.0)
    );
    assert_eq!(
        eval_aggregate_step("avg", &IncrementalValue::Number(4.0), &mut agg),
        IncrementalValue::Number(3.0)
    );

    let mut ts = TimeShiftState::default();
    assert_eq!(
        eval_time_shift_step(None, 1, &IncrementalValue::Number(10.0), &mut ts),
        IncrementalValue::Null
    );
    assert_eq!(
        eval_time_shift_step(Some("change"), 1, &IncrementalValue::Number(13.0), &mut ts),
        IncrementalValue::Number(3.0)
    );
}
