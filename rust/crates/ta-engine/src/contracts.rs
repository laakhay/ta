//! Canonical runtime contracts for Rust-first execution.

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
