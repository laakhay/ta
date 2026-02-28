//! Core runtime primitives for the Rust-first TA engine.

pub mod contracts;
pub mod dataset;
pub mod dataset_ops;
pub mod events;
pub mod incremental;
pub mod metadata;
pub mod momentum;
pub mod moving_averages;
pub mod rolling;
pub mod trend;
pub mod volatility;
pub mod volume;

pub fn engine_version() -> &'static str {
    "0.1.0"
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exposes_version() {
        assert_eq!(engine_version(), "0.1.0");
    }
}
