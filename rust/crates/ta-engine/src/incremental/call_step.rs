use std::collections::BTreeMap;

use super::contracts::IncrementalValue;
use super::kernel_registry::{coerce_incremental_input, KernelId};

#[derive(Debug, Clone, PartialEq)]
pub enum KernelRuntimeState {
    Rsi {
        period: usize,
        prev_close: Option<f64>,
        avg_gain: Option<f64>,
        avg_loss: Option<f64>,
        count: usize,
    },
    Atr {
        period: usize,
        prev_close: Option<f64>,
        rma_tr: Option<f64>,
        count: usize,
    },
    Stochastic {
        k_period: usize,
        highs: Vec<f64>,
        lows: Vec<f64>,
    },
}

pub fn initialize_kernel_state(
    kernel_id: KernelId,
    kwargs: &BTreeMap<String, IncrementalValue>,
) -> KernelRuntimeState {
    match kernel_id {
        KernelId::Rsi => KernelRuntimeState::Rsi {
            period: get_usize(kwargs, "period", 14),
            prev_close: None,
            avg_gain: None,
            avg_loss: None,
            count: 0,
        },
        KernelId::Atr => KernelRuntimeState::Atr {
            period: get_usize(kwargs, "period", 14),
            prev_close: None,
            rma_tr: None,
            count: 0,
        },
        KernelId::Stochastic => KernelRuntimeState::Stochastic {
            k_period: get_usize(kwargs, "k_period", 14),
            highs: Vec::new(),
            lows: Vec::new(),
        },
    }
}

pub fn eval_call_step(
    kernel_id: KernelId,
    state: KernelRuntimeState,
    input_value: IncrementalValue,
    tick: &BTreeMap<String, IncrementalValue>,
) -> (KernelRuntimeState, IncrementalValue) {
    match state {
        KernelRuntimeState::Rsi {
            period,
            prev_close,
            avg_gain,
            avg_loss,
            count,
        } => {
            let coerced = coerce_incremental_input(kernel_id, input_value, tick, prev_close);
            let close = match coerced {
                IncrementalValue::Number(v) => v,
                _ => {
                    return (
                        KernelRuntimeState::Rsi {
                            period,
                            prev_close,
                            avg_gain,
                            avg_loss,
                            count,
                        },
                        IncrementalValue::Null,
                    )
                }
            };

            let new_count = count + 1;
            if prev_close.is_none() {
                return (
                    KernelRuntimeState::Rsi {
                        period,
                        prev_close: Some(close),
                        avg_gain,
                        avg_loss,
                        count: new_count,
                    },
                    IncrementalValue::Null,
                );
            }

            let diff = close - prev_close.unwrap_or(close);
            let gain = if diff > 0.0 { diff } else { 0.0 };
            let loss = if diff < 0.0 { -diff } else { 0.0 };

            if avg_gain.is_none() || avg_loss.is_none() {
                return (
                    KernelRuntimeState::Rsi {
                        period,
                        prev_close: Some(close),
                        avg_gain: Some(gain),
                        avg_loss: Some(loss),
                        count: new_count,
                    },
                    IncrementalValue::Null,
                );
            }

            let ag = ((avg_gain.unwrap_or(0.0) * (period as f64 - 1.0)) + gain) / period as f64;
            let al = ((avg_loss.unwrap_or(0.0) * (period as f64 - 1.0)) + loss) / period as f64;

            let rsi = if al == 0.0 {
                if ag > 0.0 {
                    100.0
                } else {
                    50.0
                }
            } else {
                let rs = ag / al;
                100.0 - (100.0 / (1.0 + rs))
            };

            let output = if new_count < period + 1 {
                IncrementalValue::Null
            } else {
                IncrementalValue::Number(rsi.clamp(0.0, 100.0))
            };

            (
                KernelRuntimeState::Rsi {
                    period,
                    prev_close: Some(close),
                    avg_gain: Some(ag),
                    avg_loss: Some(al),
                    count: new_count,
                },
                output,
            )
        }
        KernelRuntimeState::Atr {
            period,
            prev_close,
            rma_tr,
            count,
        } => {
            let coerced = coerce_incremental_input(kernel_id, input_value, tick, prev_close);
            let tr = match coerced {
                IncrementalValue::Number(v) => v,
                _ => 0.0,
            };
            let close = get_num(tick, "close").unwrap_or(0.0);
            let new_count = count + 1;

            if rma_tr.is_none() {
                let out = if new_count < period {
                    IncrementalValue::Null
                } else {
                    IncrementalValue::Number(tr)
                };
                return (
                    KernelRuntimeState::Atr {
                        period,
                        prev_close: Some(close),
                        rma_tr: Some(tr),
                        count: new_count,
                    },
                    out,
                );
            }

            let new_rma = ((rma_tr.unwrap_or(0.0) * (period as f64 - 1.0)) + tr) / period as f64;
            let out = if new_count < period {
                IncrementalValue::Null
            } else {
                IncrementalValue::Number(new_rma)
            };

            (
                KernelRuntimeState::Atr {
                    period,
                    prev_close: Some(close),
                    rma_tr: Some(new_rma),
                    count: new_count,
                },
                out,
            )
        }
        KernelRuntimeState::Stochastic {
            k_period,
            mut highs,
            mut lows,
        } => {
            let coerced = coerce_incremental_input(kernel_id, input_value, tick, None);
            let (h, l, c) = match coerced {
                IncrementalValue::Text(s) => {
                    let parts: Vec<&str> = s.split(',').collect();
                    if parts.len() != 3 {
                        return (
                            KernelRuntimeState::Stochastic {
                                k_period,
                                highs,
                                lows,
                            },
                            IncrementalValue::Null,
                        );
                    }
                    (
                        parts[0].parse::<f64>().unwrap_or(0.0),
                        parts[1].parse::<f64>().unwrap_or(0.0),
                        parts[2].parse::<f64>().unwrap_or(0.0),
                    )
                }
                _ => {
                    return (
                        KernelRuntimeState::Stochastic {
                            k_period,
                            highs,
                            lows,
                        },
                        IncrementalValue::Null,
                    )
                }
            };

            highs.push(h);
            lows.push(l);
            if highs.len() > k_period {
                let _ = highs.remove(0);
                let _ = lows.remove(0);
            }

            if highs.len() < k_period {
                return (
                    KernelRuntimeState::Stochastic {
                        k_period,
                        highs,
                        lows,
                    },
                    IncrementalValue::Null,
                );
            }

            let hh = highs.iter().fold(f64::MIN, |a, b| a.max(*b));
            let ll = lows.iter().fold(f64::MAX, |a, b| a.min(*b));
            let denom = hh - ll;
            let k = if denom == 0.0 {
                50.0
            } else {
                100.0 * (c - ll) / denom
            };

            (
                KernelRuntimeState::Stochastic {
                    k_period,
                    highs,
                    lows,
                },
                IncrementalValue::Number(k),
            )
        }
    }
}

fn get_usize(kwargs: &BTreeMap<String, IncrementalValue>, key: &str, default: usize) -> usize {
    match kwargs.get(key) {
        Some(IncrementalValue::Number(n)) if *n > 0.0 => *n as usize,
        _ => default,
    }
}

fn get_num(tick: &BTreeMap<String, IncrementalValue>, key: &str) -> Option<f64> {
    match tick.get(key) {
        Some(IncrementalValue::Number(n)) => Some(*n),
        _ => None,
    }
}
