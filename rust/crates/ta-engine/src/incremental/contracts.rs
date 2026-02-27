use std::collections::BTreeMap;

pub const INCREMENTAL_STATE_SCHEMA_VERSION: u16 = 1;

#[derive(Debug, Clone, PartialEq)]
pub enum IncrementalValue {
    Number(f64),
    Bool(bool),
    Text(String),
    Null,
}

#[derive(Debug, Clone, PartialEq)]
pub struct TickUpdate {
    pub event_index: u64,
    pub fields: BTreeMap<String, IncrementalValue>,
}

impl TickUpdate {
    pub fn new(event_index: u64, fields: BTreeMap<String, IncrementalValue>) -> Self {
        Self {
            event_index,
            fields,
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct NodeStepResult {
    pub node_id: u32,
    pub output: IncrementalValue,
}

#[derive(Debug, Clone, PartialEq)]
pub struct RuntimeSnapshot {
    pub schema_version: u16,
    pub last_event_index: u64,
    pub nodes: BTreeMap<u32, NodeSnapshotState>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct NodeSnapshotState {
    pub ticks_processed: u64,
    pub last_output: IncrementalValue,
    pub state_blob: BTreeMap<String, IncrementalValue>,
}

impl RuntimeSnapshot {
    pub fn empty() -> Self {
        Self {
            schema_version: INCREMENTAL_STATE_SCHEMA_VERSION,
            last_event_index: 0,
            nodes: BTreeMap::new(),
        }
    }
}
