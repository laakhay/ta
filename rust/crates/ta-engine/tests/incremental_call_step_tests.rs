use std::collections::BTreeMap;

use ta_engine::incremental::call_step::{eval_call_step, initialize_kernel_state};
use ta_engine::incremental::contracts::IncrementalValue;
use ta_engine::incremental::kernel_registry::{coerce_incremental_input, KernelId};

#[test]
fn kernel_id_resolution_and_atr_coercion_work() {
    assert_eq!(KernelId::from_name("rsi"), Some(KernelId::Rsi));
    assert_eq!(KernelId::from_name("unknown"), None);

    let mut tick = BTreeMap::new();
    tick.insert("high".to_string(), IncrementalValue::Number(12.0));
    tick.insert("low".to_string(), IncrementalValue::Number(10.0));
    tick.insert("close".to_string(), IncrementalValue::Number(11.0));

    let tr = coerce_incremental_input(KernelId::Atr, IncrementalValue::Null, &tick, Some(9.0));
    assert!(matches!(tr, IncrementalValue::Number(v) if v >= 2.0));
}

#[test]
fn rsi_call_step_warms_then_outputs() {
    let mut kwargs = BTreeMap::new();
    kwargs.insert("period".to_string(), IncrementalValue::Number(2.0));
    let mut state = initialize_kernel_state(KernelId::Rsi, &kwargs);

    let prices = [10.0, 11.0, 12.0, 11.0];
    let mut output_count = 0;
    for p in prices {
        let tick = BTreeMap::from([("close".to_string(), IncrementalValue::Number(p))]);
        let (new_state, out) =
            eval_call_step(KernelId::Rsi, state, IncrementalValue::Number(p), &tick);
        state = new_state;
        if !matches!(out, IncrementalValue::Null) {
            output_count += 1;
        }
    }
    assert!(output_count > 0);
}

#[test]
fn stochastic_call_step_emits_after_window() {
    let mut kwargs = BTreeMap::new();
    kwargs.insert("k_period".to_string(), IncrementalValue::Number(3.0));
    let mut state = initialize_kernel_state(KernelId::Stochastic, &kwargs);

    let ticks = vec![(10.0, 8.0, 9.0), (11.0, 9.0, 10.0), (12.0, 9.5, 11.0)];
    let mut last = IncrementalValue::Null;
    for (h, l, c) in ticks {
        let tick = BTreeMap::from([
            ("high".to_string(), IncrementalValue::Number(h)),
            ("low".to_string(), IncrementalValue::Number(l)),
            ("close".to_string(), IncrementalValue::Number(c)),
        ]);
        let (new_state, out) =
            eval_call_step(KernelId::Stochastic, state, IncrementalValue::Null, &tick);
        state = new_state;
        last = out;
    }

    assert!(matches!(last, IncrementalValue::Number(_)));
}
