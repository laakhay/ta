use std::collections::BTreeMap;

use super::contracts::IncrementalValue;

#[derive(Debug, Clone, PartialEq)]
pub struct NodeRuntimeState {
    pub node_id: u32,
    pub ticks_processed: u64,
    pub last_output: IncrementalValue,
    pub state_blob: BTreeMap<String, IncrementalValue>,
}
