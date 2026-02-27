use std::collections::BTreeMap;

use super::call_step::{eval_call_step, initialize_kernel_state, KernelRuntimeState};
use super::contracts::{IncrementalValue, RuntimeSnapshot};
use super::kernel_registry::KernelId;
use super::state::NodeRuntimeState;
use super::store::RuntimeStateStore;

#[derive(Debug, Clone)]
pub struct KernelStepRequest {
    pub node_id: u32,
    pub kernel_id: KernelId,
    pub input_field: String,
    pub kwargs: BTreeMap<String, IncrementalValue>,
}

#[derive(Debug, Clone, Default)]
pub struct IncrementalBackend {
    store: RuntimeStateStore,
    call_states: BTreeMap<u32, KernelRuntimeState>,
}

impl IncrementalBackend {
    pub fn initialize(&mut self) {
        self.store.initialize();
        self.call_states.clear();
    }

    pub fn step(
        &mut self,
        event_index: u64,
        requests: &[KernelStepRequest],
        tick: &BTreeMap<String, IncrementalValue>,
    ) -> BTreeMap<u32, IncrementalValue> {
        self.store.set_last_event_index(event_index);
        let mut outputs = BTreeMap::new();

        for req in requests {
            let state = self
                .call_states
                .remove(&req.node_id)
                .unwrap_or_else(|| initialize_kernel_state(req.kernel_id, &req.kwargs));

            let input = tick
                .get(&req.input_field)
                .cloned()
                .unwrap_or(IncrementalValue::Null);

            let (new_state, out) = eval_call_step(req.kernel_id, state, input, tick);
            self.call_states.insert(req.node_id, new_state);
            let state_blob = self
                .call_states
                .get(&req.node_id)
                .map(encode_kernel_state)
                .unwrap_or_default();

            let ticks_processed = self
                .store
                .get_node(req.node_id)
                .map(|s| s.ticks_processed + 1)
                .unwrap_or(1);

            self.store.upsert_node(NodeRuntimeState {
                node_id: req.node_id,
                ticks_processed,
                last_output: out.clone(),
                state_blob,
            });

            outputs.insert(req.node_id, out);
        }

        outputs
    }

    pub fn snapshot(&self) -> RuntimeSnapshot {
        self.store.snapshot()
    }

    pub fn restore(&mut self, snapshot: RuntimeSnapshot) -> Result<(), &'static str> {
        self.store.restore(snapshot.clone())?;
        self.call_states.clear();
        for (node_id, node) in snapshot.nodes {
            if let Some(state) = decode_kernel_state(&node.state_blob) {
                self.call_states.insert(node_id, state);
            }
        }
        Ok(())
    }

    pub fn replay(
        &mut self,
        requests: &[KernelStepRequest],
        events: &[BTreeMap<String, IncrementalValue>],
    ) -> Vec<BTreeMap<u32, IncrementalValue>> {
        events
            .iter()
            .enumerate()
            .map(|(idx, tick)| self.step(idx as u64 + 1, requests, tick))
            .collect()
    }
}

fn encode_kernel_state(state: &KernelRuntimeState) -> BTreeMap<String, IncrementalValue> {
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
    }
    blob
}

fn decode_kernel_state(blob: &BTreeMap<String, IncrementalValue>) -> Option<KernelRuntimeState> {
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
