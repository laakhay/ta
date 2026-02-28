use std::collections::BTreeMap;

use super::call_step::KernelRuntimeState;
use super::contracts::IncrementalValue;
use super::kernel_registry::KernelId;

pub(crate) fn encode_kernel_state(
    state: &KernelRuntimeState,
) -> BTreeMap<String, IncrementalValue> {
    let mut blob = BTreeMap::new();
    match state {
        KernelRuntimeState::Rsi {
            period,
            prev_close,
            avg_gain,
            avg_loss,
            count,
        } => {
            blob.insert(
                "kind".to_string(),
                IncrementalValue::Text("rsi".to_string()),
            );
            blob.insert(
                "period".to_string(),
                IncrementalValue::Number(*period as f64),
            );
            blob.insert("count".to_string(), IncrementalValue::Number(*count as f64));
            blob.insert(
                "prev_close".to_string(),
                prev_close.map_or(IncrementalValue::Null, IncrementalValue::Number),
            );
            blob.insert(
                "avg_gain".to_string(),
                avg_gain.map_or(IncrementalValue::Null, IncrementalValue::Number),
            );
            blob.insert(
                "avg_loss".to_string(),
                avg_loss.map_or(IncrementalValue::Null, IncrementalValue::Number),
            );
        }
        KernelRuntimeState::Atr {
            period,
            prev_close,
            rma_tr,
            count,
        } => {
            blob.insert(
                "kind".to_string(),
                IncrementalValue::Text("atr".to_string()),
            );
            blob.insert(
                "period".to_string(),
                IncrementalValue::Number(*period as f64),
            );
            blob.insert("count".to_string(), IncrementalValue::Number(*count as f64));
            blob.insert(
                "prev_close".to_string(),
                prev_close.map_or(IncrementalValue::Null, IncrementalValue::Number),
            );
            blob.insert(
                "rma_tr".to_string(),
                rma_tr.map_or(IncrementalValue::Null, IncrementalValue::Number),
            );
        }
        KernelRuntimeState::Stochastic {
            k_period,
            highs,
            lows,
        } => {
            blob.insert(
                "kind".to_string(),
                IncrementalValue::Text("stochastic".to_string()),
            );
            blob.insert(
                "k_period".to_string(),
                IncrementalValue::Number(*k_period as f64),
            );
            blob.insert(
                "highs".to_string(),
                IncrementalValue::Text(
                    highs
                        .iter()
                        .map(|v| v.to_string())
                        .collect::<Vec<_>>()
                        .join(","),
                ),
            );
            blob.insert(
                "lows".to_string(),
                IncrementalValue::Text(
                    lows.iter()
                        .map(|v| v.to_string())
                        .collect::<Vec<_>>()
                        .join(","),
                ),
            );
        }
        KernelRuntimeState::Vwap {
            highs,
            lows,
            closes,
            volumes,
        } => {
            blob.insert(
                "kind".to_string(),
                IncrementalValue::Text("vwap".to_string()),
            );
            blob.insert(
                "highs".to_string(),
                IncrementalValue::Text(
                    highs
                        .iter()
                        .map(|v| v.to_string())
                        .collect::<Vec<_>>()
                        .join(","),
                ),
            );
            blob.insert(
                "lows".to_string(),
                IncrementalValue::Text(
                    lows.iter()
                        .map(|v| v.to_string())
                        .collect::<Vec<_>>()
                        .join(","),
                ),
            );
            blob.insert(
                "closes".to_string(),
                IncrementalValue::Text(
                    closes
                        .iter()
                        .map(|v| v.to_string())
                        .collect::<Vec<_>>()
                        .join(","),
                ),
            );
            blob.insert(
                "volumes".to_string(),
                IncrementalValue::Text(
                    volumes
                        .iter()
                        .map(|v| v.to_string())
                        .collect::<Vec<_>>()
                        .join(","),
                ),
            );
        }
        KernelRuntimeState::Generic { kernel_id: _ } => {
            blob.insert(
                "kind".to_string(),
                IncrementalValue::Text("generic".to_string()),
            );
        }
    }
    blob
}

pub(crate) fn decode_kernel_state(
    blob: &BTreeMap<String, IncrementalValue>,
) -> Option<KernelRuntimeState> {
    let kind = match blob.get("kind") {
        Some(IncrementalValue::Text(s)) => s.as_str(),
        _ => return None,
    };

    match kind {
        "rsi" => Some(KernelRuntimeState::Rsi {
            period: get_num(blob, "period").unwrap_or(14.0) as usize,
            prev_close: get_num(blob, "prev_close"),
            avg_gain: get_num(blob, "avg_gain"),
            avg_loss: get_num(blob, "avg_loss"),
            count: get_num(blob, "count").unwrap_or(0.0) as usize,
        }),
        "atr" => Some(KernelRuntimeState::Atr {
            period: get_num(blob, "period").unwrap_or(14.0) as usize,
            prev_close: get_num(blob, "prev_close"),
            rma_tr: get_num(blob, "rma_tr"),
            count: get_num(blob, "count").unwrap_or(0.0) as usize,
        }),
        "stochastic" => Some(KernelRuntimeState::Stochastic {
            k_period: get_num(blob, "k_period").unwrap_or(14.0) as usize,
            highs: get_csv_nums(blob, "highs"),
            lows: get_csv_nums(blob, "lows"),
        }),
        "vwap" => Some(KernelRuntimeState::Vwap {
            highs: get_csv_nums(blob, "highs"),
            lows: get_csv_nums(blob, "lows"),
            closes: get_csv_nums(blob, "closes"),
            volumes: get_csv_nums(blob, "volumes"),
        }),
        "generic" => Some(KernelRuntimeState::Generic {
            kernel_id: KernelId::Rsi,
        }),
        _ => None,
    }
}

fn get_num(blob: &BTreeMap<String, IncrementalValue>, key: &str) -> Option<f64> {
    match blob.get(key) {
        Some(IncrementalValue::Number(v)) => Some(*v),
        _ => None,
    }
}

fn get_csv_nums(blob: &BTreeMap<String, IncrementalValue>, key: &str) -> Vec<f64> {
    match blob.get(key) {
        Some(IncrementalValue::Text(s)) if !s.is_empty() => {
            s.split(',').filter_map(|v| v.parse::<f64>().ok()).collect()
        }
        _ => Vec::new(),
    }
}
