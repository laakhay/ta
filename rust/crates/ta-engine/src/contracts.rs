//! Canonical runtime contracts for Rust-first execution.

use std::collections::BTreeMap;

use crate::incremental::contracts::IncrementalValue;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum TaStatusCode {
    Ok = 0,
    InvalidInput = 1,
    ShapeMismatch = 2,
    InternalError = 255,
}

#[derive(Debug, Clone, PartialEq)]
pub struct TaSeriesF64 {
    pub values: Vec<f64>,
    pub availability_mask: Vec<bool>,
}

impl TaSeriesF64 {
    pub fn new(values: Vec<f64>, availability_mask: Vec<bool>) -> Result<Self, TaStatusCode> {
        if values.len() != availability_mask.len() {
            return Err(TaStatusCode::ShapeMismatch);
        }
        Ok(Self {
            values,
            availability_mask,
        })
    }

    pub fn len(&self) -> usize {
        self.values.len()
    }

    pub fn is_empty(&self) -> bool {
        self.values.is_empty()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RustExecutionPartition {
    pub symbol: String,
    pub timeframe: String,
    pub source: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RustExecutionGraph {
    pub root_id: u32,
    pub node_order: Vec<u32>,
    pub nodes: BTreeMap<u32, BTreeMap<String, String>>,
    pub edges: BTreeMap<u32, Vec<u32>>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct RustExecutionRequest {
    pub node_id: u32,
    pub kernel_id: String,
    pub input_field: String,
    pub kwargs: BTreeMap<String, IncrementalValue>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct RustExecutionPayload {
    pub dataset_id: u64,
    pub partition: RustExecutionPartition,
    pub graph: RustExecutionGraph,
    pub requests: Vec<RustExecutionRequest>,
}

impl RustExecutionPayload {
    pub fn validate(&self) -> Result<(), String> {
        if self.partition.symbol.trim().is_empty() {
            return Err("partition.symbol must be non-empty".to_string());
        }
        if self.partition.timeframe.trim().is_empty() {
            return Err("partition.timeframe must be non-empty".to_string());
        }
        if self.partition.source.trim().is_empty() {
            return Err("partition.source must be non-empty".to_string());
        }
        if self.graph.node_order.is_empty() {
            return Err("graph.node_order must be non-empty".to_string());
        }
        if !self.graph.nodes.contains_key(&self.graph.root_id) {
            return Err("graph.root_id must exist in graph.nodes".to_string());
        }
        if !self.graph.node_order.contains(&self.graph.root_id) {
            return Err("graph.root_id must be present in graph.node_order".to_string());
        }
        for node_id in self.graph.nodes.keys() {
            if !self.graph.node_order.contains(node_id) {
                return Err(format!(
                    "graph.node_order missing node id present in graph.nodes: {node_id}"
                ));
            }
        }
        Ok(())
    }
}
