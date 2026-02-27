use std::collections::BTreeMap;

use super::contracts::IncrementalValue;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceRef {
    pub source: String,
    pub field: String,
}

pub fn eval_source_ref_step(
    node: &SourceRef,
    tick: &BTreeMap<String, IncrementalValue>,
) -> IncrementalValue {
    let key1 = format!("{}.{}", node.source, node.field);
    if let Some(v) = tick.get(&key1) {
        return v.clone();
    }
    if let Some(v) = tick.get(&node.field) {
        return v.clone();
    }
    IncrementalValue::Null
}

pub fn eval_literal_step(value: &IncrementalValue) -> IncrementalValue {
    value.clone()
}

pub fn eval_binary_step(
    op: &str,
    left: &IncrementalValue,
    right: &IncrementalValue,
) -> IncrementalValue {
    match (op, left, right) {
        (_, IncrementalValue::Null, _) | (_, _, IncrementalValue::Null) => IncrementalValue::Null,
        ("add", IncrementalValue::Number(l), IncrementalValue::Number(r)) => {
            IncrementalValue::Number(l + r)
        }
        ("sub", IncrementalValue::Number(l), IncrementalValue::Number(r)) => {
            IncrementalValue::Number(l - r)
        }
        ("mul", IncrementalValue::Number(l), IncrementalValue::Number(r)) => {
            IncrementalValue::Number(l * r)
        }
        ("div", IncrementalValue::Number(_), IncrementalValue::Number(r)) if *r == 0.0 => {
            IncrementalValue::Number(0.0)
        }
        ("div", IncrementalValue::Number(l), IncrementalValue::Number(r)) => {
            IncrementalValue::Number(l / r)
        }
        ("eq", IncrementalValue::Number(l), IncrementalValue::Number(r)) => {
            IncrementalValue::Bool(l == r)
        }
        ("gt", IncrementalValue::Number(l), IncrementalValue::Number(r)) => {
            IncrementalValue::Bool(l > r)
        }
        ("lt", IncrementalValue::Number(l), IncrementalValue::Number(r)) => {
            IncrementalValue::Bool(l < r)
        }
        ("and", l, r) => IncrementalValue::Bool(truthy(l) && truthy(r)),
        ("or", l, r) => IncrementalValue::Bool(truthy(l) || truthy(r)),
        _ => IncrementalValue::Null,
    }
}

pub fn eval_unary_step(op: &str, value: &IncrementalValue) -> IncrementalValue {
    match (op, value) {
        (_, IncrementalValue::Null) => IncrementalValue::Null,
        ("neg", IncrementalValue::Number(v)) => IncrementalValue::Number(-v),
        ("pos", IncrementalValue::Number(v)) => IncrementalValue::Number(*v),
        ("not", v) => IncrementalValue::Bool(!truthy(v)),
        _ => IncrementalValue::Null,
    }
}

pub fn eval_filter_step(
    value: &IncrementalValue,
    condition: &IncrementalValue,
) -> IncrementalValue {
    if truthy(condition) {
        value.clone()
    } else {
        IncrementalValue::Null
    }
}

#[derive(Debug, Clone, Default, PartialEq)]
pub struct AggregateState {
    pub count: u64,
    pub sum: f64,
    pub max: Option<f64>,
    pub min: Option<f64>,
}

pub fn eval_aggregate_step(
    op: &str,
    value: &IncrementalValue,
    state: &mut AggregateState,
) -> IncrementalValue {
    if let IncrementalValue::Number(v) = value {
        state.count += 1;
        state.sum += *v;
        state.max = Some(state.max.map_or(*v, |m| m.max(*v)));
        state.min = Some(state.min.map_or(*v, |m| m.min(*v)));
    }

    match op {
        "count" => IncrementalValue::Number(state.count as f64),
        "sum" => IncrementalValue::Number(state.sum),
        "avg" if state.count > 0 => IncrementalValue::Number(state.sum / state.count as f64),
        "avg" => IncrementalValue::Null,
        "max" => state
            .max
            .map_or(IncrementalValue::Null, IncrementalValue::Number),
        "min" => state
            .min
            .map_or(IncrementalValue::Null, IncrementalValue::Number),
        _ => IncrementalValue::Null,
    }
}

#[derive(Debug, Clone, Default, PartialEq)]
pub struct TimeShiftState {
    pub history: Vec<IncrementalValue>,
}

pub fn eval_time_shift_step(
    operation: Option<&str>,
    periods: usize,
    value: &IncrementalValue,
    state: &mut TimeShiftState,
) -> IncrementalValue {
    if periods == 0 {
        return IncrementalValue::Null;
    }

    let out = if state.history.len() >= periods {
        let prev = &state.history[state.history.len() - periods];
        match (operation, value, prev) {
            (None, _, _) => prev.clone(),
            (Some("change"), IncrementalValue::Number(curr), IncrementalValue::Number(pr)) => {
                IncrementalValue::Number(curr - pr)
            }
            (Some("change_pct"), IncrementalValue::Number(curr), IncrementalValue::Number(pr))
                if *pr == 0.0 =>
            {
                IncrementalValue::Number(0.0)
            }
            (Some("change_pct"), IncrementalValue::Number(curr), IncrementalValue::Number(pr)) => {
                IncrementalValue::Number(((curr - pr) / pr) * 100.0)
            }
            _ => IncrementalValue::Null,
        }
    } else {
        IncrementalValue::Null
    };

    state.history.push(value.clone());
    if state.history.len() > periods + 1 {
        let _ = state.history.remove(0);
    }

    out
}

fn truthy(v: &IncrementalValue) -> bool {
    match v {
        IncrementalValue::Null => false,
        IncrementalValue::Bool(b) => *b,
        IncrementalValue::Number(n) => *n != 0.0,
        IncrementalValue::Text(s) => !s.is_empty(),
    }
}
