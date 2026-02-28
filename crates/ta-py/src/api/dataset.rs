use pyo3::prelude::*;
use pyo3::types::PyDict;
use ta_engine::dataset::{self, DatasetPartitionKey};

use crate::conversions::indicator_meta_to_pydict;
use crate::errors::{map_dataset_error, map_dataset_ops_error};

#[pyfunction]
pub(crate) fn engine_version() -> &'static str {
    ta_engine::engine_version()
}

#[pyfunction]
pub(crate) fn dataset_create() -> u64 {
    dataset::create_dataset()
}

#[pyfunction]
pub(crate) fn dataset_drop(dataset_id: u64) -> PyResult<()> {
    dataset::drop_dataset(dataset_id).map_err(map_dataset_error)
}

#[pyfunction]
#[allow(clippy::too_many_arguments)]
pub(crate) fn dataset_append_ohlcv(
    dataset_id: u64,
    symbol: String,
    timeframe: String,
    source: String,
    timestamps: Vec<i64>,
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
) -> PyResult<usize> {
    dataset::append_ohlcv(
        dataset_id,
        DatasetPartitionKey {
            symbol,
            timeframe,
            source,
        },
        &timestamps,
        &open,
        &high,
        &low,
        &close,
        &volume,
    )
    .map_err(map_dataset_error)
}

#[pyfunction]
pub(crate) fn dataset_append_series(
    dataset_id: u64,
    symbol: String,
    timeframe: String,
    source: String,
    field: String,
    timestamps: Vec<i64>,
    values: Vec<f64>,
) -> PyResult<usize> {
    dataset::append_series(
        dataset_id,
        DatasetPartitionKey {
            symbol,
            timeframe,
            source,
        },
        field,
        &timestamps,
        &values,
    )
    .map_err(map_dataset_error)
}

#[pyfunction]
pub(crate) fn dataset_info(py: Python<'_>, dataset_id: u64) -> PyResult<PyObject> {
    let info = dataset::dataset_info(dataset_id).map_err(map_dataset_error)?;
    let out = PyDict::new(py);
    out.set_item("id", info.id)?;
    out.set_item("partition_count", info.partition_count)?;
    out.set_item("ohlcv_row_count", info.ohlcv_row_count)?;
    out.set_item("series_row_count", info.series_row_count)?;
    out.set_item("series_count", info.series_count)?;
    Ok(out.into_any().unbind())
}

#[pyfunction]
pub(crate) fn series_downsample(
    timestamps: Vec<i64>,
    values: Vec<f64>,
    factor: usize,
    agg: String,
) -> PyResult<(Vec<i64>, Vec<f64>)> {
    ta_engine::dataset_ops::downsample(&timestamps, &values, factor, &agg)
        .map_err(map_dataset_ops_error)
}

#[pyfunction]
pub(crate) fn series_upsample_ffill(
    timestamps: Vec<i64>,
    values: Vec<f64>,
    factor: usize,
) -> PyResult<(Vec<i64>, Vec<f64>)> {
    ta_engine::dataset_ops::upsample_ffill(&timestamps, &values, factor)
        .map_err(map_dataset_ops_error)
}

#[pyfunction]
pub(crate) fn series_sync_timeframe(
    source_timestamps: Vec<i64>,
    source_values: Vec<f64>,
    reference_timestamps: Vec<i64>,
    fill: String,
) -> PyResult<Vec<f64>> {
    ta_engine::dataset_ops::sync_timeframe(
        &source_timestamps,
        &source_values,
        &reference_timestamps,
        &fill,
    )
    .map_err(map_dataset_ops_error)
}

#[pyfunction]
pub(crate) fn indicator_catalog(py: Python<'_>) -> PyResult<PyObject> {
    let py_list = pyo3::types::PyList::empty(py);
    for meta in ta_engine::metadata::indicator_catalog() {
        py_list.append(indicator_meta_to_pydict(py, meta)?)?;
    }
    Ok(py_list.into_any().unbind())
}

#[pyfunction]
pub(crate) fn indicator_catalog_contract(py: Python<'_>) -> PyResult<PyObject> {
    let out = PyDict::new(py);
    out.set_item("contract_version", 1)?;
    out.set_item("indicators", indicator_catalog(py)?)?;
    Ok(out.into_any().unbind())
}

#[pyfunction]
pub(crate) fn indicator_meta(py: Python<'_>, id: String) -> PyResult<PyObject> {
    let meta = ta_engine::metadata::find_indicator_meta(&id).ok_or_else(|| {
        pyo3::exceptions::PyKeyError::new_err(format!(
            "indicator metadata not found for id/alias '{id}'"
        ))
    })?;
    indicator_meta_to_pydict(py, meta)
}
