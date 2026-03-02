mod catalog;
mod compute;
mod contracts;
mod params;

pub use catalog::runtime_catalog;
pub use compute::compute_indicator;
pub use contracts::{
    ComputeIndicatorRequest, ComputeIndicatorResponse, ComputeRuntimeError, NamedSeries,
    OhlcvInput, RuntimeCatalogEntry,
};
