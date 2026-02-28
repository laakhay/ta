use std::collections::BTreeMap;

use super::contracts::{NodeSnapshotState, RuntimeSnapshot, INCREMENTAL_STATE_SCHEMA_VERSION};
use super::state::NodeRuntimeState;

#[derive(Debug, Clone, Default)]
pub struct RuntimeStateStore {
    last_event_index: u64,
    nodes: BTreeMap<u32, NodeRuntimeState>,
}

impl RuntimeStateStore {
    pub fn initialize(&mut self) {
        self.last_event_index = 0;
        self.nodes.clear();
    }

    pub fn set_last_event_index(&mut self, event_index: u64) {
        self.last_event_index = event_index;
    }

    pub fn upsert_node(&mut self, node: NodeRuntimeState) {
        self.nodes.insert(node.node_id, node);
    }

    pub fn get_node(&self, node_id: u32) -> Option<&NodeRuntimeState> {
        self.nodes.get(&node_id)
    }

    pub fn snapshot(&self) -> RuntimeSnapshot {
        let mut nodes: BTreeMap<u32, NodeSnapshotState> = BTreeMap::new();
        for (node_id, state) in &self.nodes {
            nodes.insert(
                *node_id,
                NodeSnapshotState {
                    ticks_processed: state.ticks_processed,
                    last_output: state.last_output.clone(),
                    state_blob: state.state_blob.clone(),
                },
            );
        }

        RuntimeSnapshot {
            schema_version: INCREMENTAL_STATE_SCHEMA_VERSION,
            last_event_index: self.last_event_index,
            nodes,
        }
    }

    pub fn restore(&mut self, snapshot: RuntimeSnapshot) -> Result<(), &'static str> {
        if snapshot.schema_version != INCREMENTAL_STATE_SCHEMA_VERSION {
            return Err("unsupported snapshot schema version");
        }

        self.last_event_index = snapshot.last_event_index;
        self.nodes = snapshot
            .nodes
            .into_iter()
            .map(|(node_id, node)| {
                (
                    node_id,
                    NodeRuntimeState {
                        node_id,
                        ticks_processed: node.ticks_processed,
                        last_output: node.last_output,
                        state_blob: node.state_blob,
                    },
                )
            })
            .collect();

        Ok(())
    }
}
