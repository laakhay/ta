//! Core runtime primitives for the Rust-first TA engine.

pub mod core;
pub mod execution;
pub mod indicators;
pub mod runtime;

pub use core::{contracts, dataset, dataset_ops, events, metadata};
pub use execution::incremental;
pub use indicators::{momentum, moving_averages, rolling, trend, volatility, volume};
pub use runtime::{
    compute_indicator, runtime_catalog, ComputeIndicatorRequest, ComputeIndicatorResponse,
    ComputeRuntimeError, NamedSeries, OhlcvInput, RuntimeCatalogEntry,
};

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
