use std::collections::BTreeMap;

use crate::contracts::RustExecutionPayload;
use crate::dataset::{self, DatasetPartitionKey};

use super::backend::ExecutePlanError;
use super::contracts::IncrementalValue;

pub(crate) fn execute_plan_graph_payload(
    payload: &RustExecutionPayload,
) -> Result<BTreeMap<u32, Vec<IncrementalValue>>, ExecutePlanError> {
    payload
        .validate()
        .map_err(ExecutePlanError::InvalidPayload)?;
    let record = dataset::get_dataset(payload.dataset_id)?;
    let partition_key = DatasetPartitionKey {
        symbol: payload.partition.symbol.clone(),
        timeframe: payload.partition.timeframe.clone(),
        source: payload.partition.source.clone(),
    };
    let partition = record.partitions.get(&partition_key).ok_or_else(|| {
        ExecutePlanError::PartitionNotFound {
            symbol: partition_key.symbol.clone(),
            timeframe: partition_key.timeframe.clone(),
            data_source: partition_key.source.clone(),
        }
    })?;
    let rows = partition
        .ohlcv
        .as_ref()
        .map(|ohlcv| ohlcv.timestamps.len())
        .or_else(|| partition.series.values().next().map(|s| s.timestamps.len()))
        .ok_or_else(|| ExecutePlanError::MissingOhlcv {
            symbol: partition_key.symbol.clone(),
            timeframe: partition_key.timeframe.clone(),
            data_source: partition_key.source.clone(),
        })?;
    let mut outputs: BTreeMap<u32, Vec<IncrementalValue>> = BTreeMap::new();

    for node_id in &payload.graph.node_order {
        let meta = payload.graph.nodes.get(node_id).ok_or_else(|| {
            ExecutePlanError::InvalidPayload(format!("missing node metadata for id {node_id}"))
        })?;
        let kind = meta.get("kind").ok_or_else(|| {
            ExecutePlanError::InvalidPayload(format!("missing node kind for id {node_id}"))
        })?;
        let child_ids = payload
            .graph
            .edges
            .get(node_id)
            .cloned()
            .unwrap_or_default();

        let series = match kind.as_str() {
            "source_ref" => {
                let field = meta
                    .get("field")
                    .cloned()
                    .unwrap_or_else(|| "close".to_string());
                let source_name = meta.get("source").cloned().unwrap_or_default();
                if let Some(series) = partition.series.get(&field) {
                    series
                        .values
                        .iter()
                        .copied()
                        .map(IncrementalValue::Number)
                        .collect()
                } else if let Some(series) = partition.series.get(&source_name) {
                    series
                        .values
                        .iter()
                        .copied()
                        .map(IncrementalValue::Number)
                        .collect()
                } else {
                    match field.as_str() {
                        "open" => partition
                            .ohlcv
                            .as_ref()
                            .map(|ohlcv| {
                                ohlcv
                                    .open
                                    .iter()
                                    .copied()
                                    .map(IncrementalValue::Number)
                                    .collect()
                            })
                            .ok_or_else(|| {
                                ExecutePlanError::MissingOhlcv {
                                    symbol: partition_key.symbol.clone(),
                                    timeframe: partition_key.timeframe.clone(),
                                    data_source: partition_key.source.clone(),
                                }
                            })?,
                        "high" => partition
                            .ohlcv
                            .as_ref()
                            .map(|ohlcv| {
                                ohlcv
                                    .high
                                    .iter()
                                    .copied()
                                    .map(IncrementalValue::Number)
                                    .collect()
                            })
                            .ok_or_else(|| {
                                ExecutePlanError::MissingOhlcv {
                                    symbol: partition_key.symbol.clone(),
                                    timeframe: partition_key.timeframe.clone(),
                                    data_source: partition_key.source.clone(),
                                }
                            })?,
                        "low" => partition
                            .ohlcv
                            .as_ref()
                            .map(|ohlcv| {
                                ohlcv
                                    .low
                                    .iter()
                                    .copied()
                                    .map(IncrementalValue::Number)
                                    .collect()
                            })
                            .ok_or_else(|| {
                                ExecutePlanError::MissingOhlcv {
                                    symbol: partition_key.symbol.clone(),
                                    timeframe: partition_key.timeframe.clone(),
                                    data_source: partition_key.source.clone(),
                                }
                            })?,
                        "volume" => partition
                            .ohlcv
                            .as_ref()
                            .map(|ohlcv| {
                                ohlcv
                                    .volume
                                    .iter()
                                    .copied()
                                    .map(IncrementalValue::Number)
                                    .collect()
                            })
                            .ok_or_else(|| {
                                ExecutePlanError::MissingOhlcv {
                                    symbol: partition_key.symbol.clone(),
                                    timeframe: partition_key.timeframe.clone(),
                                    data_source: partition_key.source.clone(),
                                }
                            })?,
                        _ => partition
                            .ohlcv
                            .as_ref()
                            .map(|ohlcv| {
                                ohlcv
                                    .close
                                    .iter()
                                    .copied()
                                    .map(IncrementalValue::Number)
                                    .collect()
                            })
                            .ok_or_else(|| {
                                ExecutePlanError::MissingOhlcv {
                                    symbol: partition_key.symbol.clone(),
                                    timeframe: partition_key.timeframe.clone(),
                                    data_source: partition_key.source.clone(),
                                }
                            })?,
                    }
                }
            }
            "literal" => {
                let value_str = meta
                    .get("value")
                    .cloned()
                    .unwrap_or_else(|| "0".to_string());
                if value_str.eq_ignore_ascii_case("true") {
                    vec![IncrementalValue::Bool(true); rows]
                } else if value_str.eq_ignore_ascii_case("false") {
                    vec![IncrementalValue::Bool(false); rows]
                } else if let Ok(value) = value_str.parse::<f64>() {
                    vec![IncrementalValue::Number(value); rows]
                } else {
                    vec![IncrementalValue::Text(value_str); rows]
                }
            }
            "call" => {
                let name = meta
                    .get("name")
                    .cloned()
                    .unwrap_or_else(|| "unknown".to_string());
                if name == "select" && partition.ohlcv.is_none() {
                    let field = meta
                        .get("kw_field")
                        .or_else(|| meta.get("field"))
                        .or_else(|| meta.get("arg_0"))
                        .map(|v| v.as_str())
                        .unwrap_or("close");
                    if let Some(series) = partition.series.get(field) {
                        series
                            .values
                            .iter()
                            .copied()
                            .map(IncrementalValue::Number)
                            .collect()
                    } else {
                        return Err(ExecutePlanError::InvalidPayload(format!(
                            "select could not resolve source field '{field}'"
                        )));
                    }
                } else {
                let child_series = child_ids
                    .iter()
                    .map(|input_id| {
                        let child_kind = payload
                            .graph
                            .nodes
                            .get(input_id)
                            .and_then(|n| n.get("kind"))
                            .cloned()
                            .unwrap_or_default();
                        if child_kind == "literal" {
                            Ok(
                                partition
                                    .ohlcv
                                    .as_ref()
                                    .map(|v| v.close.clone())
                                    .or_else(|| partition.series.values().next().map(|s| s.values.clone()))
                                    .unwrap_or_default(),
                            )
                        } else {
                            let input_values = outputs.get(input_id).ok_or_else(|| {
                                ExecutePlanError::InvalidPayload(format!(
                                    "missing input output for node {input_id}"
                                ))
                            })?;
                            Ok(to_f64_vec(input_values))
                        }
                    })
                    .collect::<Result<Vec<Vec<f64>>, ExecutePlanError>>()?;
                dispatch_call_node(&name, meta, &child_series, partition.ohlcv.as_ref())?
                }
            }
            "time_shift" => {
                if child_ids.is_empty() {
                    return Err(ExecutePlanError::InvalidPayload(format!(
                        "time_shift node {node_id} requires one child"
                    )));
                }
                let base = outputs.get(&child_ids[0]).ok_or_else(|| {
                    ExecutePlanError::InvalidPayload(format!(
                        "missing time_shift child output for node {}",
                        child_ids[0]
                    ))
                })?;
                let steps = parse_shift_steps(meta.get("shift").map(|s| s.as_str()).unwrap_or("1")).max(1);
                let operation = meta.get("operation").map(|s| s.as_str()).unwrap_or("change");
                apply_time_shift_op(base, steps, operation)
            }
            "binary_op" => {
                if child_ids.len() < 2 {
                    return Err(ExecutePlanError::InvalidPayload(format!(
                        "binary node {node_id} requires two children"
                    )));
                }
                let left = outputs.get(&child_ids[0]).ok_or_else(|| {
                    ExecutePlanError::InvalidPayload(format!(
                        "missing left child output for node {}",
                        child_ids[0]
                    ))
                })?;
                let right = outputs.get(&child_ids[1]).ok_or_else(|| {
                    ExecutePlanError::InvalidPayload(format!(
                        "missing right child output for node {}",
                        child_ids[1]
                    ))
                })?;
                let op = meta
                    .get("operator")
                    .cloned()
                    .unwrap_or_else(|| "eq".to_string());
                left.iter()
                    .zip(right.iter())
                    .map(|(l, r)| match op.as_str() {
                        "gt" => IncrementalValue::Bool(as_number(l) > as_number(r)),
                        "gte" => IncrementalValue::Bool(as_number(l) >= as_number(r)),
                        "lt" => IncrementalValue::Bool(as_number(l) < as_number(r)),
                        "lte" => IncrementalValue::Bool(as_number(l) <= as_number(r)),
                        "eq" => IncrementalValue::Bool(as_number(l) == as_number(r)),
                        "neq" => IncrementalValue::Bool(as_number(l) != as_number(r)),
                        "and" => IncrementalValue::Bool(truthy(l) && truthy(r)),
                        "or" => IncrementalValue::Bool(truthy(l) || truthy(r)),
                        "add" => IncrementalValue::Number(as_number(l) + as_number(r)),
                        "sub" => IncrementalValue::Number(as_number(l) - as_number(r)),
                        "mul" => IncrementalValue::Number(as_number(l) * as_number(r)),
                        "mod" => IncrementalValue::Number(as_number(l) % as_number(r)),
                        "pow" => IncrementalValue::Number(as_number(l).powf(as_number(r))),
                        "div" => {
                            let rv = as_number(r);
                            if rv == 0.0 {
                                IncrementalValue::Number(0.0)
                            } else {
                                IncrementalValue::Number(as_number(l) / rv)
                            }
                        }
                        _ => IncrementalValue::Null,
                    })
                    .collect()
            }
            "unary_op" => {
                if child_ids.is_empty() {
                    return Err(ExecutePlanError::InvalidPayload(format!(
                        "unary node {node_id} requires one child"
                    )));
                }
                let input = outputs.get(&child_ids[0]).ok_or_else(|| {
                    ExecutePlanError::InvalidPayload(format!(
                        "missing unary child output for node {}",
                        child_ids[0]
                    ))
                })?;
                let op = meta
                    .get("operator")
                    .cloned()
                    .unwrap_or_else(|| "pos".to_string());
                input
                    .iter()
                    .map(|v| match op.as_str() {
                        "not" => IncrementalValue::Bool(!truthy(v)),
                        "neg" => IncrementalValue::Number(-as_number(v)),
                        _ => IncrementalValue::Number(as_number(v)),
                    })
                    .collect()
            }
            "filter" => {
                if child_ids.len() < 2 {
                    return Err(ExecutePlanError::InvalidPayload(format!(
                        "filter node {node_id} requires two children"
                    )));
                }
                let input = outputs.get(&child_ids[0]).ok_or_else(|| {
                    ExecutePlanError::InvalidPayload(format!(
                        "missing filter input for node {}",
                        child_ids[0]
                    ))
                })?;
                let condition = outputs.get(&child_ids[1]).ok_or_else(|| {
                    ExecutePlanError::InvalidPayload(format!(
                        "missing filter condition for node {}",
                        child_ids[1]
                    ))
                })?;
                input
                    .iter()
                    .zip(condition.iter())
                    .map(|(value, cond)| {
                        if truthy(cond) {
                            value.clone()
                        } else {
                            IncrementalValue::Null
                        }
                    })
                    .collect()
            }
            "aggregate" => {
                if child_ids.is_empty() {
                    return Err(ExecutePlanError::InvalidPayload(format!(
                        "aggregate node {node_id} requires one child"
                    )));
                }
                let input = outputs.get(&child_ids[0]).ok_or_else(|| {
                    ExecutePlanError::InvalidPayload(format!(
                        "missing aggregate input for node {}",
                        child_ids[0]
                    ))
                })?;
                let operation = meta
                    .get("operation")
                    .cloned()
                    .unwrap_or_else(|| "sum".to_string());
                let non_null: Vec<&IncrementalValue> = input
                    .iter()
                    .filter(|v| !matches!(v, IncrementalValue::Null))
                    .collect();
                let aggregated = match operation.as_str() {
                    "count" => IncrementalValue::Number(non_null.len() as f64),
                    "sum" => IncrementalValue::Number(non_null.iter().map(|v| as_number(v)).sum()),
                    "avg" => {
                        if non_null.is_empty() {
                            IncrementalValue::Null
                        } else {
                            let sum: f64 = non_null.iter().map(|v| as_number(v)).sum();
                            IncrementalValue::Number(sum / non_null.len() as f64)
                        }
                    }
                    "max" => {
                        let max = non_null
                            .iter()
                            .map(|v| as_number(v))
                            .fold(f64::NAN, f64::max);
                        if max.is_nan() {
                            IncrementalValue::Null
                        } else {
                            IncrementalValue::Number(max)
                        }
                    }
                    "min" => {
                        let min = non_null
                            .iter()
                            .map(|v| as_number(v))
                            .fold(f64::NAN, f64::min);
                        if min.is_nan() {
                            IncrementalValue::Null
                        } else {
                            IncrementalValue::Number(min)
                        }
                    }
                    other => {
                        return Err(ExecutePlanError::InvalidPayload(format!(
                            "unsupported aggregate operation: {other}"
                        )))
                    }
                };
                vec![aggregated; rows]
            }
            other => {
                return Err(ExecutePlanError::InvalidPayload(format!(
                    "unsupported graph node kind: {other}"
                )))
            }
        };
        outputs.insert(*node_id, series);
    }

    Ok(outputs)
}

fn to_f64_vec(values: &[IncrementalValue]) -> Vec<f64> {
    values.iter().map(as_number).collect()
}

fn as_number(value: &IncrementalValue) -> f64 {
    match value {
        IncrementalValue::Number(v) => *v,
        IncrementalValue::Bool(v) => {
            if *v {
                1.0
            } else {
                0.0
            }
        }
        IncrementalValue::Text(v) => v.parse::<f64>().unwrap_or(0.0),
        IncrementalValue::Null => f64::NAN,
    }
}

fn truthy(value: &IncrementalValue) -> bool {
    match value {
        IncrementalValue::Null => false,
        IncrementalValue::Bool(v) => *v,
        IncrementalValue::Number(v) => *v != 0.0 && !v.is_nan(),
        IncrementalValue::Text(v) => !v.is_empty(),
    }
}

fn parse_shift_steps(shift: &str) -> usize {
    let digits: String = shift.chars().take_while(|c| c.is_ascii_digit()).collect();
    digits.parse::<usize>().unwrap_or(1)
}

fn apply_time_shift_op(base: &[IncrementalValue], steps: usize, operation: &str) -> Vec<IncrementalValue> {
    let mut out = vec![IncrementalValue::Null; base.len()];
    for i in steps..base.len() {
        let cur = as_number(&base[i]);
        let prev = as_number(&base[i - steps]);
        out[i] = match operation {
            "change_pct" => {
                if prev == 0.0 || prev.is_nan() || cur.is_nan() {
                    IncrementalValue::Null
                } else {
                    IncrementalValue::Number(((cur - prev) / prev) * 100.0)
                }
            }
            _ => {
                if prev.is_nan() || cur.is_nan() {
                    IncrementalValue::Null
                } else {
                    IncrementalValue::Number(cur - prev)
                }
            }
        };
    }
    out
}

fn dispatch_call_node(
    name: &str,
    meta: &BTreeMap<String, String>,
    child_series: &[Vec<f64>],
    ohlcv: Option<&crate::dataset::OhlcvColumns>,
) -> Result<Vec<IncrementalValue>, ExecutePlanError> {
    let normalized = name.trim().to_ascii_lowercase();
    let name = normalized.as_str();
    let selected_output = meta.get("output").map(|v| v.as_str());
    let default_close = ohlcv.map(|v| v.close.clone()).unwrap_or_default();
    let close = child_series.first().cloned().unwrap_or_else(|| default_close.clone());
    let second = child_series
        .get(1)
        .cloned()
        .unwrap_or_else(|| default_close.clone());
    let third = child_series
        .get(2)
        .cloned()
        .unwrap_or_else(|| default_close.clone());

    let to_num = |values: Vec<f64>| values.into_iter().map(IncrementalValue::Number).collect();
    let to_bool = |values: Vec<bool>| values.into_iter().map(IncrementalValue::Bool).collect();

    let out = match name {
        "select" => {
            let field = meta
                .get("kw_field")
                .or_else(|| meta.get("field"))
                .or_else(|| meta.get("arg_0"))
                .map(|v| v.as_str())
                .unwrap_or("close");
            if ohlcv.is_none() {
                if close.is_empty() {
                    return Err(ExecutePlanError::InvalidPayload(format!(
                        "select could not resolve source field '{field}'"
                    )));
                }
                return Ok(close.iter().copied().map(IncrementalValue::Number).collect());
            }
            match (field, ohlcv) {
                ("open", Some(v)) => v.open.iter().copied().map(IncrementalValue::Number).collect(),
                ("high", Some(v)) => v.high.iter().copied().map(IncrementalValue::Number).collect(),
                ("low", Some(v)) => v.low.iter().copied().map(IncrementalValue::Number).collect(),
                ("volume", Some(v)) => v.volume.iter().copied().map(IncrementalValue::Number).collect(),
                ("close", Some(v)) | ("price", Some(v)) => {
                    v.close.iter().copied().map(IncrementalValue::Number).collect()
                }
                _ => close.iter().copied().map(IncrementalValue::Number).collect(),
            }
        }
        "sma" | "mean" | "rolling_mean" => {
            let period = get_usize(meta, "period", "arg_0", 20);
            to_num(crate::rolling::rolling_mean(&close, period))
        }
        "rolling_median" | "median" => {
            let period = get_usize(meta, "period", "arg_0", 20);
            to_num(crate::rolling::rolling_median(&close, period))
        }
        "ema" | "rolling_ema" => {
            let period = get_usize(meta, "period", "arg_0", 20);
            to_num(crate::moving_averages::ema(&close, period))
        }
        "wma" | "rolling_wma" => {
            let period = get_usize(meta, "period", "arg_0", 14);
            to_num(crate::moving_averages::wma(&close, period))
        }
        "hma" => {
            let period = get_usize(meta, "period", "arg_0", 14);
            to_num(crate::moving_averages::hma(&close, period))
        }
        "rsi" => {
            let period = get_usize(meta, "period", "arg_0", 14);
            to_num(crate::momentum::rsi(&close, period))
        }
        "roc" => {
            let period = get_usize(meta, "period", "arg_0", 12);
            to_num(crate::momentum::roc(&close, period))
        }
        "coppock" => {
            let wma_period = get_usize(meta, "wma_period", "arg_0", 10);
            let fast_roc = get_usize(meta, "fast_roc", "arg_1", 11);
            let slow_roc = get_usize(meta, "slow_roc", "arg_2", 14);
            to_num(crate::momentum::coppock(&close, wma_period, fast_roc, slow_roc))
        }
        "cmo" => {
            let period = get_usize(meta, "period", "arg_0", 14);
            to_num(crate::momentum::cmo(&close, period))
        }
        "mfi" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("mfi requires ohlcv data".to_string())
            })?;
            let period = get_usize(meta, "period", "arg_0", 14);
            to_num(crate::momentum::mfi(
                &ohlcv.high,
                &ohlcv.low,
                &ohlcv.close,
                &ohlcv.volume,
                period,
            ))
        }
        "vortex" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("vortex requires ohlcv data".to_string())
            })?;
            let period = get_usize(meta, "period", "arg_0", 14);
            let (plus, minus) = crate::momentum::vortex(&ohlcv.high, &ohlcv.low, &ohlcv.close, period);
            match selected_output {
                Some("minus") => to_num(minus),
                _ => to_num(plus),
            }
        }
        "bbands" | "bb_upper" | "bb_lower" => {
            let period = get_usize(meta, "period", "arg_0", 20);
            let std_dev = get_f64(meta, "std_dev", "arg_1", 2.0);
            let (upper, _middle, lower) = crate::volatility::bbands(&close, period, std_dev);
            match name {
                "bb_upper" => to_num(upper),
                "bb_lower" => to_num(lower),
                _ => to_num(upper),
            }
        }
        "atr" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("atr requires ohlcv data".to_string())
            })?;
            let period = get_usize(meta, "period", "arg_0", 14);
            to_num(crate::volatility::atr(
                &ohlcv.high,
                &ohlcv.low,
                &ohlcv.close,
                period,
            ))
        }
        "donchian" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("donchian requires ohlcv data".to_string())
            })?;
            let period = get_usize(meta, "period", "arg_0", 20);
            let (upper, _middle, _lower) = crate::volatility::donchian(&ohlcv.high, &ohlcv.low, period);
            to_num(upper)
        }
        "keltner" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("keltner requires ohlcv data".to_string())
            })?;
            let ema_period = get_usize(meta, "ema_period", "arg_0", 20);
            let atr_period = get_usize(meta, "atr_period", "arg_1", 10);
            let multiplier = get_f64(meta, "multiplier", "arg_2", 2.0);
            let (upper, _middle, _lower) = crate::volatility::keltner(
                &ohlcv.high,
                &ohlcv.low,
                &ohlcv.close,
                ema_period,
                atr_period,
                multiplier,
            );
            to_num(upper)
        }
        "stochastic" | "stoch_k" | "stoch_d" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("stochastic requires ohlcv data".to_string())
            })?;
            let k_period = get_usize(meta, "k_period", "arg_0", 14);
            let d_period = get_usize(meta, "d_period", "arg_1", 3);
            let smooth = get_usize(meta, "smooth", "arg_2", 1);
            let (k, d) =
                crate::momentum::stochastic_kd(&ohlcv.high, &ohlcv.low, &ohlcv.close, k_period, d_period, smooth);
            match name {
                "stoch_d" => to_num(d),
                _ => to_num(k),
            }
        }
        "adx" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("adx requires ohlcv data".to_string())
            })?;
            let period = get_usize(meta, "period", "arg_0", 14);
            let (adx, _, _) = crate::trend::adx(&ohlcv.high, &ohlcv.low, &ohlcv.close, period);
            to_num(adx)
        }
        "macd" => {
            let fast = get_usize(meta, "fast_period", "arg_0", 12);
            let slow = get_usize(meta, "slow_period", "arg_1", 26);
            let signal = get_usize(meta, "signal_period", "arg_2", 9);
            let (macd, signal_line, histogram) = crate::trend::macd(&close, fast, slow, signal);
            match selected_output {
                Some("signal") => to_num(signal_line),
                Some("histogram") => to_num(histogram),
                _ => to_num(macd),
            }
        }
        "elder_ray" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("elder_ray requires ohlcv data".to_string())
            })?;
            let period = get_usize(meta, "period", "arg_0", 13);
            let (bull, bear) = crate::trend::elder_ray(&ohlcv.high, &ohlcv.low, &ohlcv.close, period);
            match selected_output {
                Some("bear") => to_num(bear),
                _ => to_num(bull),
            }
        }
        "fisher" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("fisher requires ohlcv data".to_string())
            })?;
            let period = get_usize(meta, "period", "arg_0", 9);
            let (fisher, signal) = crate::trend::fisher(&ohlcv.high, &ohlcv.low, period);
            match selected_output {
                Some("signal") => to_num(signal),
                _ => to_num(fisher),
            }
        }
        "ichimoku" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("ichimoku requires ohlcv data".to_string())
            })?;
            let tenkan_period = get_usize(meta, "tenkan_period", "arg_0", 9);
            let kijun_period = get_usize(meta, "kijun_period", "arg_1", 26);
            let span_b_period = get_usize(meta, "span_b_period", "arg_2", 52);
            let displacement = get_usize(meta, "displacement", "arg_3", 26);
            let (tenkan, kijun, span_a, span_b, chikou) = crate::trend::ichimoku(
                &ohlcv.high,
                &ohlcv.low,
                &ohlcv.close,
                tenkan_period,
                kijun_period,
                span_b_period,
                displacement,
            );
            match selected_output {
                Some("kijun_sen") => to_num(kijun),
                Some("senkou_span_a") => to_num(span_a),
                Some("senkou_span_b") => to_num(span_b),
                Some("chikou_span") => to_num(chikou),
                _ => to_num(tenkan),
            }
        }
        "psar" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("psar requires ohlcv data".to_string())
            })?;
            let af_start = get_f64(meta, "af_start", "arg_0", 0.02);
            let af_increment = get_f64(meta, "af_increment", "arg_1", 0.02);
            let af_max = get_f64(meta, "af_max", "arg_2", 0.2);
            let (sar, direction) =
                crate::trend::psar(&ohlcv.high, &ohlcv.low, &ohlcv.close, af_start, af_increment, af_max);
            match selected_output {
                Some("direction") => to_num(direction),
                _ => to_num(sar),
            }
        }
        "supertrend" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("supertrend requires ohlcv data".to_string())
            })?;
            let period = get_usize(meta, "period", "arg_0", 10);
            let multiplier = get_f64(meta, "multiplier", "arg_1", 3.0);
            let (supertrend, direction) =
                crate::trend::supertrend(&ohlcv.high, &ohlcv.low, &ohlcv.close, period, multiplier);
            match selected_output {
                Some("direction") => to_num(direction),
                _ => to_num(supertrend),
            }
        }
        "swing_high_at" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("swing_high_at requires ohlcv data".to_string())
            })?;
            let left = get_usize(meta, "left", "arg_1", 2);
            let right = get_usize(meta, "right", "arg_2", 2);
            let period = left + right + 1;
            to_num(crate::rolling::rolling_max(&ohlcv.high, period))
        }
        "swing_low_at" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("swing_low_at requires ohlcv data".to_string())
            })?;
            let left = get_usize(meta, "left", "arg_1", 2);
            let right = get_usize(meta, "right", "arg_2", 2);
            let period = left + right + 1;
            to_num(crate::rolling::rolling_min(&ohlcv.low, period))
        }
        "fib_level_down" | "fib_down" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("fib_level_down requires ohlcv data".to_string())
            })?;
            let level = get_f64(meta, "level", "arg_0", 0.618);
            let left = get_usize(meta, "left", "arg_1", 2);
            let right = get_usize(meta, "right", "arg_2", 2);
            let period = left + right + 1;
            let highs = crate::rolling::rolling_max(&ohlcv.high, period);
            let lows = crate::rolling::rolling_min(&ohlcv.low, period);
            to_num(
                highs
                    .iter()
                    .zip(lows.iter())
                    .map(|(h, l)| {
                        if h.is_nan() || l.is_nan() {
                            f64::NAN
                        } else {
                            h - ((h - l) * level)
                        }
                    })
                    .collect(),
            )
        }
        "fib_level_up" => {
            let ohlcv = ohlcv.ok_or_else(|| {
                ExecutePlanError::InvalidPayload("fib_level_up requires ohlcv data".to_string())
            })?;
            let level = get_f64(meta, "level", "arg_0", 0.618);
            let left = get_usize(meta, "left", "arg_1", 2);
            let right = get_usize(meta, "right", "arg_2", 2);
            let period = left + right + 1;
            let highs = crate::rolling::rolling_max(&ohlcv.high, period);
            let lows = crate::rolling::rolling_min(&ohlcv.low, period);
            to_num(
                highs
                    .iter()
                    .zip(lows.iter())
                    .map(|(h, l)| {
                        if h.is_nan() || l.is_nan() {
                            f64::NAN
                        } else {
                            l + ((h - l) * level)
                        }
                    })
                    .collect(),
            )
        }
        "crossup" => to_bool(crate::events::crossup(&close, &second)),
        "crossdown" => to_bool(crate::events::crossdown(&close, &second)),
        "cross" => to_bool(crate::events::cross(&close, &second)),
        "rising" => to_bool(crate::events::rising(&close)),
        "falling" => to_bool(crate::events::falling(&close)),
        "rising_pct" => {
            let pct = get_f64(meta, "pct", "arg_0", 5.0);
            to_bool(crate::events::rising_pct(&close, pct))
        }
        "falling_pct" => {
            let pct = get_f64(meta, "pct", "arg_0", 5.0);
            to_bool(crate::events::falling_pct(&close, pct))
        }
        "in_channel" => to_bool(crate::events::in_channel(&close, &second, &third)),
        "out" => to_bool(crate::events::out_channel(&close, &second, &third)),
        "enter" => to_bool(crate::events::enter_channel(&close, &second, &third)),
        "exit" => to_bool(crate::events::exit_channel(&close, &second, &third)),
        other => {
            return Err(ExecutePlanError::InvalidPayload(format!(
                "unsupported call node in graph executor: {other}"
            )))
        }
    };

    Ok(out)
}

fn get_usize(meta: &BTreeMap<String, String>, kw: &str, arg: &str, default: usize) -> usize {
    meta.get(&format!("kw_{kw}"))
        .or_else(|| meta.get(arg))
        .and_then(|v| v.parse::<usize>().ok())
        .unwrap_or(default)
}

fn get_f64(meta: &BTreeMap<String, String>, kw: &str, arg: &str, default: f64) -> f64 {
    meta.get(&format!("kw_{kw}"))
        .or_else(|| meta.get(arg))
        .and_then(|v| v.parse::<f64>().ok())
        .unwrap_or(default)
}
