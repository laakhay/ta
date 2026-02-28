use pyo3::PyErr;
use ta_engine::dataset::DatasetRegistryError;
use ta_engine::dataset_ops::DatasetOpsError;
use ta_engine::incremental::backend::ExecutePlanError;

pub(crate) fn map_execute_plan_error(err: ExecutePlanError) -> PyErr {
    match err {
        ExecutePlanError::Dataset(inner) => map_dataset_error(inner),
        ExecutePlanError::PartitionNotFound {
            symbol,
            timeframe,
            data_source,
        } => pyo3::exceptions::PyKeyError::new_err(format!(
            "dataset partition not found for symbol={symbol} timeframe={timeframe} source={data_source}"
        )),
        ExecutePlanError::MissingOhlcv {
            symbol,
            timeframe,
            data_source,
        } => pyo3::exceptions::PyValueError::new_err(format!(
            "ohlcv columns missing for symbol={symbol} timeframe={timeframe} source={data_source}"
        )),
        ExecutePlanError::InvalidPayload(message) => {
            pyo3::exceptions::PyValueError::new_err(format!("invalid execute payload: {message}"))
        }
        ExecutePlanError::UnsupportedKernelId(kernel_id) => {
            pyo3::exceptions::PyValueError::new_err(format!("unsupported kernel_id in payload: {kernel_id}"))
        }
    }
}

pub(crate) fn map_dataset_ops_error(err: DatasetOpsError) -> PyErr {
    match err {
        DatasetOpsError::LengthMismatch => pyo3::exceptions::PyValueError::new_err(
            "timestamps and values must have identical lengths",
        ),
        DatasetOpsError::InvalidFactor => {
            pyo3::exceptions::PyValueError::new_err("factor must be positive")
        }
        DatasetOpsError::UnsupportedAggregation(agg) => {
            pyo3::exceptions::PyValueError::new_err(format!("unsupported aggregation: {agg}"))
        }
        DatasetOpsError::UnsupportedFillMode(fill) => {
            pyo3::exceptions::PyValueError::new_err(format!("unsupported sync fill mode: {fill}"))
        }
    }
}

pub(crate) fn map_dataset_error(err: DatasetRegistryError) -> PyErr {
    match err {
        DatasetRegistryError::UnknownDatasetId(id) => {
            pyo3::exceptions::PyKeyError::new_err(format!("unknown dataset id: {id}"))
        }
        DatasetRegistryError::LengthMismatch {
            field,
            expected,
            got,
        } => pyo3::exceptions::PyValueError::new_err(format!(
            "length mismatch for {field}: expected {expected}, got {got}"
        )),
        DatasetRegistryError::NonMonotonicTimestamps { field } => {
            pyo3::exceptions::PyValueError::new_err(format!(
                "timestamps must be non-decreasing for {field}"
            ))
        }
        DatasetRegistryError::EmptyField { field } => {
            pyo3::exceptions::PyValueError::new_err(format!("empty field not allowed: {field}"))
        }
    }
}
