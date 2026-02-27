use std::collections::BTreeMap;

use super::contracts::IncrementalValue;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum KernelId {
    Rsi,
    Atr,
    Stochastic,
}

impl KernelId {
    pub fn from_name(name: &str) -> Option<Self> {
        match name {
            "rsi" => Some(Self::Rsi),
            "atr" => Some(Self::Atr),
            "stochastic" => Some(Self::Stochastic),
            _ => None,
        }
    }
}

pub fn coerce_incremental_input(
    kernel_id: KernelId,
    input_value: IncrementalValue,
    tick: &BTreeMap<String, IncrementalValue>,
    prev_close: Option<f64>,
) -> IncrementalValue {
    match kernel_id {
        KernelId::Atr => {
            let high = get_num(tick, "high").unwrap_or(0.0);
            let low = get_num(tick, "low").unwrap_or(0.0);
            let close = get_num(tick, "close").unwrap_or(0.0);

            let mut tr = high - low;
            if let Some(prev) = prev_close {
                tr = tr.max((high - prev).abs()).max((low - prev).abs());
            }
            let _ = close;
            IncrementalValue::Number(tr)
        }
        KernelId::Stochastic => {
            let h = get_num(tick, "high").unwrap_or(0.0);
            let l = get_num(tick, "low").unwrap_or(0.0);
            let c = get_num(tick, "close").unwrap_or(0.0);
            IncrementalValue::Text(format!("{h},{l},{c}"))
        }
        KernelId::Rsi => input_value,
    }
}

fn get_num(tick: &BTreeMap<String, IncrementalValue>, key: &str) -> Option<f64> {
    match tick.get(key) {
        Some(IncrementalValue::Number(n)) => Some(*n),
        _ => None,
    }
}
