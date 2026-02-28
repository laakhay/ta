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
    let ohlcv = partition
        .ohlcv
        .as_ref()
        .ok_or_else(|| ExecutePlanError::MissingOhlcv {
            symbol: partition_key.symbol.clone(),
            timeframe: partition_key.timeframe.clone(),
            data_source: partition_key.source.clone(),
        })?;
    let rows = ohlcv.timestamps.len();
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
                match field.as_str() {
                    "open" => ohlcv
                        .open
                        .iter()
                        .copied()
                        .map(IncrementalValue::Number)
                        .collect(),
                    "high" => ohlcv
                        .high
                        .iter()
                        .copied()
                        .map(IncrementalValue::Number)
                        .collect(),
                    "low" => ohlcv
                        .low
                        .iter()
                        .copied()
                        .map(IncrementalValue::Number)
                        .collect(),
                    "volume" => ohlcv
                        .volume
                        .iter()
                        .copied()
                        .map(IncrementalValue::Number)
                        .collect(),
                    _ => ohlcv
                        .close
                        .iter()
                        .copied()
                        .map(IncrementalValue::Number)
                        .collect(),
                }
            }
            "literal" => {
                let value_str = meta
                    .get("value")
                    .cloned()
                    .unwrap_or_else(|| "0".to_string());
                let value = value_str.parse::<f64>().unwrap_or(0.0);
                vec![IncrementalValue::Number(value); rows]
            }
            "call" => {
                let name = meta
                    .get("name")
                    .cloned()
                    .unwrap_or_else(|| "unknown".to_string());
                let input = if let Some(input_id) = child_ids.first() {
                    let child_kind = payload
                        .graph
                        .nodes
                        .get(input_id)
                        .and_then(|n| n.get("kind"))
                        .cloned()
                        .unwrap_or_default();
                    if child_kind == "literal" {
                        ohlcv.close.clone()
                    } else {
                        let input_values = outputs.get(input_id).ok_or_else(|| {
                            ExecutePlanError::InvalidPayload(format!(
                                "missing input output for node {input_id}"
                            ))
                        })?;
                        to_f64_vec(input_values)
                    }
                } else {
                    ohlcv.close.clone()
                };
                match name.as_str() {
                    "sma" | "mean" | "rolling_mean" => {
                        let period = meta
                            .get("kw_period")
                            .or_else(|| meta.get("arg_0"))
                            .and_then(|v| v.parse::<usize>().ok())
                            .unwrap_or(20);
                        crate::rolling::rolling_mean(&input, period)
                            .into_iter()
                            .map(IncrementalValue::Number)
                            .collect()
                    }
                    "rsi" => {
                        let period = meta
                            .get("kw_period")
                            .or_else(|| meta.get("arg_0"))
                            .and_then(|v| v.parse::<usize>().ok())
                            .unwrap_or(14);
                        crate::momentum::rsi(&input, period)
                            .into_iter()
                            .map(IncrementalValue::Number)
                            .collect()
                    }
                    other => {
                        return Err(ExecutePlanError::InvalidPayload(format!(
                            "unsupported call node in graph executor: {other}"
                        )))
                    }
                }
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
                        "lt" => IncrementalValue::Bool(as_number(l) < as_number(r)),
                        "eq" => IncrementalValue::Bool(as_number(l) == as_number(r)),
                        "and" => IncrementalValue::Bool(truthy(l) && truthy(r)),
                        "or" => IncrementalValue::Bool(truthy(l) || truthy(r)),
                        "add" => IncrementalValue::Number(as_number(l) + as_number(r)),
                        "sub" => IncrementalValue::Number(as_number(l) - as_number(r)),
                        "mul" => IncrementalValue::Number(as_number(l) * as_number(r)),
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
