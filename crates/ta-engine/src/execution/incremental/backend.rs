use std::collections::BTreeMap;

use super::call_step::{eval_call_step, initialize_kernel_state, KernelRuntimeState};
use super::contracts::{IncrementalValue, RuntimeSnapshot};
use super::graph_exec;
use super::kernel_registry::KernelId;
use super::payload_parse;
use super::state::NodeRuntimeState;
use super::state_codec;
use super::store::RuntimeStateStore;
use crate::contracts::RustExecutionPayload;
use crate::dataset::{self, DatasetId, DatasetPartitionKey};
use thiserror::Error;

#[derive(Debug, Clone)]
pub struct KernelStepRequest {
    pub node_id: u32,
    pub kernel_id: KernelId,
    pub input_field: String,
    pub kwargs: BTreeMap<String, IncrementalValue>,
}

#[derive(Debug, Clone)]
pub struct ExecutePlanPayload {
    pub dataset_id: DatasetId,
    pub partition_key: DatasetPartitionKey,
    pub requests: Vec<KernelStepRequest>,
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
                .map(state_codec::encode_kernel_state)
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
            if let Some(state) = state_codec::decode_kernel_state(&node.state_blob) {
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

#[derive(Debug, Error, PartialEq, Eq)]
pub enum ExecutePlanError {
    #[error(transparent)]
    Dataset(#[from] dataset::DatasetRegistryError),
    #[error("dataset partition not found for symbol={symbol} timeframe={timeframe} source={data_source}")]
    PartitionNotFound {
        symbol: String,
        timeframe: String,
        data_source: String,
    },
    #[error(
        "ohlcv columns missing for symbol={symbol} timeframe={timeframe} source={data_source}"
    )]
    MissingOhlcv {
        symbol: String,
        timeframe: String,
        data_source: String,
    },
    #[error("invalid execute payload: {0}")]
    InvalidPayload(String),
    #[error("unsupported kernel_id in payload: {0}")]
    UnsupportedKernelId(String),
}

pub fn execute_plan(
    dataset_id: DatasetId,
    partition_key: &DatasetPartitionKey,
    requests: &[KernelStepRequest],
) -> Result<BTreeMap<u32, Vec<IncrementalValue>>, ExecutePlanError> {
    let record = dataset::get_dataset(dataset_id)?;
    let partition = record.partitions.get(partition_key).ok_or_else(|| {
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

    let mut backend = IncrementalBackend::default();
    backend.initialize();

    let mut out: BTreeMap<u32, Vec<IncrementalValue>> = BTreeMap::new();
    for node in requests {
        out.entry(node.node_id).or_default();
    }

    let rows = ohlcv.timestamps.len();
    for idx in 0..rows {
        let mut tick = BTreeMap::new();
        tick.insert(
            "open".to_string(),
            IncrementalValue::Number(ohlcv.open[idx]),
        );
        tick.insert(
            "high".to_string(),
            IncrementalValue::Number(ohlcv.high[idx]),
        );
        tick.insert("low".to_string(), IncrementalValue::Number(ohlcv.low[idx]));
        tick.insert(
            "close".to_string(),
            IncrementalValue::Number(ohlcv.close[idx]),
        );
        tick.insert(
            "volume".to_string(),
            IncrementalValue::Number(ohlcv.volume[idx]),
        );

        let step_out = backend.step((idx as u64) + 1, requests, &tick);
        for (node_id, value) in step_out {
            out.entry(node_id).or_default().push(value);
        }
    }

    Ok(out)
}

pub fn execute_plan_payload(
    payload: &ExecutePlanPayload,
) -> Result<BTreeMap<u32, Vec<IncrementalValue>>, ExecutePlanError> {
    execute_plan(
        payload.dataset_id,
        &payload.partition_key,
        &payload.requests,
    )
}

pub fn parse_execute_plan_payload(
    payload: &RustExecutionPayload,
) -> Result<ExecutePlanPayload, ExecutePlanError> {
    payload_parse::parse_execute_plan_payload(payload)
}

pub fn execute_plan_graph_payload(
    payload: &RustExecutionPayload,
) -> Result<BTreeMap<u32, Vec<IncrementalValue>>, ExecutePlanError> {
    graph_exec::execute_plan_graph_payload(payload)
}
