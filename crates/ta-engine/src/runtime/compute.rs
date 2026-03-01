use super::contracts::{ComputeIndicatorRequest, ComputeIndicatorResponse, ComputeRuntimeError};
use super::params::normalize_params;

pub fn compute_indicator(
    req: ComputeIndicatorRequest,
) -> Result<ComputeIndicatorResponse, ComputeRuntimeError> {
    req.ohlcv.validate()?;
    let _normalized_params = normalize_params(&req.params)?;
    Err(ComputeRuntimeError::new(
        "unsupported_indicator",
        format!(
            "generic runtime compute is not implemented yet for '{}'",
            req.indicator_id
        ),
    ))
}
