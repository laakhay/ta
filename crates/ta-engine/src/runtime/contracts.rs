use std::fmt;

use serde_json::Value;

use crate::core::metadata::{
    ComputeCapability, IndicatorMeta, IndicatorVisualMeta, PlotCapability,
};

#[derive(Debug, Clone, PartialEq)]
pub struct OhlcvInput {
    pub timestamps: Vec<i64>,
    pub open: Vec<f64>,
    pub high: Vec<f64>,
    pub low: Vec<f64>,
    pub close: Vec<f64>,
    pub volume: Option<Vec<f64>>,
}

impl OhlcvInput {
    pub fn len(&self) -> usize {
        self.timestamps.len()
    }

    pub fn is_empty(&self) -> bool {
        self.timestamps.is_empty()
    }

    pub fn validate(&self) -> Result<(), ComputeRuntimeError> {
        let expected = self.timestamps.len();
        ensure_len("open", self.open.len(), expected)?;
        ensure_len("high", self.high.len(), expected)?;
        ensure_len("low", self.low.len(), expected)?;
        ensure_len("close", self.close.len(), expected)?;
        if let Some(volume) = &self.volume {
            ensure_len("volume", volume.len(), expected)?;
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct ComputeIndicatorRequest {
    pub indicator_id: String,
    pub params: Value,
    pub ohlcv: OhlcvInput,
    pub instance_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct NamedSeries {
    pub name: String,
    pub values: Vec<Option<f64>>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct ComputeIndicatorResponse {
    pub indicator_id: String,
    pub runtime_binding: String,
    pub instance_id: Option<String>,
    pub outputs: Vec<NamedSeries>,
    pub visual: IndicatorVisualMeta,
    pub normalized_params: Value,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RuntimeCatalogEntry {
    pub id: String,
    pub display_name: String,
    pub category: String,
    pub aliases: Vec<String>,
    pub runtime_binding: String,
    pub plot_capability: PlotCapability,
    pub compute_capability: ComputeCapability,
    pub input_requirements: Vec<String>,
}

impl RuntimeCatalogEntry {
    pub fn from_meta(meta: &IndicatorMeta) -> Self {
        Self {
            id: meta.id.to_string(),
            display_name: meta.display_name.to_string(),
            category: meta.category.to_string(),
            aliases: meta.aliases.iter().map(|v| (*v).to_string()).collect(),
            runtime_binding: meta.runtime_binding.to_string(),
            plot_capability: crate::core::metadata::plot_capability(meta),
            compute_capability: crate::core::metadata::compute_capability(meta),
            input_requirements: meta
                .semantics
                .required_fields
                .iter()
                .map(|v| (*v).to_string())
                .collect(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ComputeRuntimeError {
    pub code: String,
    pub message: String,
}

impl ComputeRuntimeError {
    pub fn new(code: &str, message: impl Into<String>) -> Self {
        Self {
            code: code.to_string(),
            message: message.into(),
        }
    }
}

impl fmt::Display for ComputeRuntimeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}: {}", self.code, self.message)
    }
}

impl std::error::Error for ComputeRuntimeError {}

fn ensure_len(field: &'static str, got: usize, expected: usize) -> Result<(), ComputeRuntimeError> {
    if got == expected {
        return Ok(());
    }
    Err(ComputeRuntimeError::new(
        "invalid_input",
        format!("{field} length mismatch: expected {expected}, got {got}"),
    ))
}
