use std::collections::{BTreeMap, HashMap};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, OnceLock};

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use ta_engine::incremental::backend::{IncrementalBackend, KernelStepRequest};
use ta_engine::incremental::contracts::{IncrementalValue, RuntimeSnapshot};
use ta_engine::incremental::kernel_registry::KernelId;

static BACKEND_ID: AtomicU64 = AtomicU64::new(1);
static SNAPSHOT_ID: AtomicU64 = AtomicU64::new(1);
static BACKENDS: OnceLock<Mutex<HashMap<u64, IncrementalBackend>>> = OnceLock::new();
static SNAPSHOTS: OnceLock<Mutex<HashMap<u64, RuntimeSnapshot>>> = OnceLock::new();

fn backends() -> &'static Mutex<HashMap<u64, IncrementalBackend>> {
    BACKENDS.get_or_init(|| Mutex::new(HashMap::new()))
}

fn snapshots() -> &'static Mutex<HashMap<u64, RuntimeSnapshot>> {
    SNAPSHOTS.get_or_init(|| Mutex::new(HashMap::new()))
}

#[pyfunction]
fn engine_version() -> &'static str {
    ta_engine::engine_version()
}

fn validate_period(period: usize) -> PyResult<()> {
    if period == 0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "period must be positive",
        ));
    }
    Ok(())
}

#[pyfunction]
fn rolling_sum(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_sum(&values, period))
}

#[pyfunction]
fn rolling_mean(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_mean(&values, period))
}

#[pyfunction]
fn rolling_std(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_std(&values, period))
}

#[pyfunction]
fn rolling_min(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_min(&values, period))
}

#[pyfunction]
fn rolling_max(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_max(&values, period))
}

#[pyfunction]
fn rolling_ema(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::moving_averages::ema(&values, period))
}

#[pyfunction]
fn rolling_rma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::moving_averages::rma(&values, period))
}

#[pyfunction]
fn rolling_wma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::moving_averages::wma(&values, period))
}

#[pyfunction]
fn rsi(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::momentum::rsi(&values, period))
}

#[pyfunction]
fn atr(high: Vec<f64>, low: Vec<f64>, close: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::volatility::atr(&high, &low, &close, period))
}

#[pyfunction]
fn atr_from_tr(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::volatility::atr_from_tr(&values, period))
}

#[pyfunction]
fn stochastic_kd(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    k_period: usize,
    d_period: usize,
    smooth: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(k_period)?;
    validate_period(d_period)?;
    validate_period(smooth)?;
    Ok(ta_engine::momentum::stochastic_kd(
        &high, &low, &close, k_period, d_period, smooth,
    ))
}

#[pyfunction]
fn obv(close: Vec<f64>, volume: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(ta_engine::volume::obv(&close, &volume))
}

#[pyfunction]
fn macd(
    values: Vec<f64>,
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_period(fast_period)?;
    validate_period(slow_period)?;
    validate_period(signal_period)?;
    Ok(ta_engine::trend::macd(
        &values,
        fast_period,
        slow_period,
        signal_period,
    ))
}

#[pyfunction]
fn bbands(
    values: Vec<f64>,
    period: usize,
    std_dev: f64,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::volatility::bbands(&values, period, std_dev))
}

#[pyfunction]
fn adx(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::trend::adx(&high, &low, &close, period))
}

#[pyfunction]
fn swing_points_raw(
    high: Vec<f64>,
    low: Vec<f64>,
    left: usize,
    right: usize,
    allow_equal_extremes: bool,
) -> PyResult<(Vec<bool>, Vec<bool>)> {
    Ok(ta_engine::trend::swing_points_raw(
        &high,
        &low,
        left,
        right,
        allow_equal_extremes,
    ))
}

#[pyfunction]
fn cci(high: Vec<f64>, low: Vec<f64>, close: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    Ok(ta_engine::momentum::cci(&high, &low, &close, period))
}

#[pyfunction]
fn vwap(high: Vec<f64>, low: Vec<f64>, close: Vec<f64>, volume: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(ta_engine::volume::vwap(&high, &low, &close, &volume))
}

#[pyfunction]
fn klinger_vf(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(ta_engine::volume::klinger_vf(&high, &low, &close, &volume))
}

#[pyfunction]
fn cmf(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    period: usize,
) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::volume::cmf(&high, &low, &close, &volume, period))
}

#[pyfunction]
fn incremental_initialize() -> PyResult<u64> {
    let mut backend = IncrementalBackend::default();
    backend.initialize();

    let id = BACKEND_ID.fetch_add(1, Ordering::SeqCst);
    let mut map = backends().lock().map_err(|_| {
        pyo3::exceptions::PyRuntimeError::new_err("failed to lock backend registry")
    })?;
    map.insert(id, backend);
    Ok(id)
}

#[pyfunction]
fn incremental_step(
    py: Python<'_>,
    backend_id: u64,
    requests: &Bound<'_, PyList>,
    tick: &Bound<'_, PyDict>,
    event_index: u64,
) -> PyResult<PyObject> {
    let mut map = backends().lock().map_err(|_| {
        pyo3::exceptions::PyRuntimeError::new_err("failed to lock backend registry")
    })?;
    let backend = map.get_mut(&backend_id).ok_or_else(|| {
        pyo3::exceptions::PyKeyError::new_err(format!("backend id {backend_id} not found"))
    })?;

    let parsed_requests = parse_requests(requests)?;
    let parsed_tick = parse_tick(tick)?;
    let out = backend.step(event_index, &parsed_requests, &parsed_tick);
    incremental_map_to_pydict(py, &out)
}

#[pyfunction]
fn incremental_snapshot(backend_id: u64) -> PyResult<u64> {
    let map = backends().lock().map_err(|_| {
        pyo3::exceptions::PyRuntimeError::new_err("failed to lock backend registry")
    })?;
    let backend = map.get(&backend_id).ok_or_else(|| {
        pyo3::exceptions::PyKeyError::new_err(format!("backend id {backend_id} not found"))
    })?;

    let snapshot = backend.snapshot();
    let snapshot_id = SNAPSHOT_ID.fetch_add(1, Ordering::SeqCst);

    let mut snaps = snapshots().lock().map_err(|_| {
        pyo3::exceptions::PyRuntimeError::new_err("failed to lock snapshot registry")
    })?;
    snaps.insert(snapshot_id, snapshot);
    Ok(snapshot_id)
}

#[pyfunction]
fn incremental_replay(
    py: Python<'_>,
    backend_id: u64,
    snapshot_id: u64,
    requests: &Bound<'_, PyList>,
    events: &Bound<'_, PyList>,
) -> PyResult<PyObject> {
    let snapshot = {
        let snaps = snapshots().lock().map_err(|_| {
            pyo3::exceptions::PyRuntimeError::new_err("failed to lock snapshot registry")
        })?;
        snaps.get(&snapshot_id).cloned().ok_or_else(|| {
            pyo3::exceptions::PyKeyError::new_err(format!("snapshot id {snapshot_id} not found"))
        })?
    };

    let parsed_requests = parse_requests(requests)?;
    let parsed_events = parse_events(events)?;

    let mut map = backends().lock().map_err(|_| {
        pyo3::exceptions::PyRuntimeError::new_err("failed to lock backend registry")
    })?;
    let backend = map.get_mut(&backend_id).ok_or_else(|| {
        pyo3::exceptions::PyKeyError::new_err(format!("backend id {backend_id} not found"))
    })?;

    backend
        .restore(snapshot)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let replay_out = backend.replay(&parsed_requests, &parsed_events);

    let py_list = PyList::empty(py);
    for step in replay_out {
        py_list.append(incremental_map_to_pydict(py, &step)?)?;
    }
    Ok(py_list.into_any().unbind())
}

fn parse_requests(requests: &Bound<'_, PyList>) -> PyResult<Vec<KernelStepRequest>> {
    let mut out = Vec::with_capacity(requests.len());
    for item in requests.iter() {
        let d = item.downcast::<PyDict>()?;
        let node_id: u32 = d
            .get_item("node_id")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing node_id"))?
            .extract()?;
        let kernel_name: String = d
            .get_item("kernel_id")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing kernel_id"))?
            .extract()?;
        let input_field: String = d
            .get_item("input_field")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing input_field"))?
            .extract()?;
        let kwargs_dict = d
            .get_item("kwargs")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing kwargs"))?
            .downcast_into::<PyDict>()?;

        let kernel_id = KernelId::from_name(&kernel_name).ok_or_else(|| {
            pyo3::exceptions::PyValueError::new_err(format!("unsupported kernel_id: {kernel_name}"))
        })?;

        out.push(KernelStepRequest {
            node_id,
            kernel_id,
            input_field,
            kwargs: parse_tick(&kwargs_dict)?,
        });
    }
    Ok(out)
}

fn parse_events(events: &Bound<'_, PyList>) -> PyResult<Vec<BTreeMap<String, IncrementalValue>>> {
    let mut out = Vec::with_capacity(events.len());
    for item in events.iter() {
        let d = item.downcast::<PyDict>()?;
        out.push(parse_tick(d)?);
    }
    Ok(out)
}

fn parse_tick(tick: &Bound<'_, PyDict>) -> PyResult<BTreeMap<String, IncrementalValue>> {
    let mut out = BTreeMap::new();
    for (k, v) in tick.iter() {
        let key: String = k.extract()?;
        let value = if let Ok(n) = v.extract::<f64>() {
            IncrementalValue::Number(n)
        } else if let Ok(b) = v.extract::<bool>() {
            IncrementalValue::Bool(b)
        } else if let Ok(s) = v.extract::<String>() {
            IncrementalValue::Text(s)
        } else {
            IncrementalValue::Null
        };
        out.insert(key, value);
    }
    Ok(out)
}

fn incremental_map_to_pydict(
    py: Python<'_>,
    values: &BTreeMap<u32, IncrementalValue>,
) -> PyResult<PyObject> {
    let d = PyDict::new(py);
    for (k, v) in values {
        match v {
            IncrementalValue::Number(n) => d.set_item(k, n)?,
            IncrementalValue::Bool(b) => d.set_item(k, b)?,
            IncrementalValue::Text(s) => d.set_item(k, s)?,
            IncrementalValue::Null => d.set_item(k, py.None())?,
        }
    }
    Ok(d.into_any().unbind())
}

#[pymodule]
fn ta_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(engine_version, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_sum, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_mean, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_std, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_min, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_max, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_ema, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_rma, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_wma, m)?)?;
    m.add_function(wrap_pyfunction!(rsi, m)?)?;
    m.add_function(wrap_pyfunction!(atr, m)?)?;
    m.add_function(wrap_pyfunction!(atr_from_tr, m)?)?;
    m.add_function(wrap_pyfunction!(stochastic_kd, m)?)?;
    m.add_function(wrap_pyfunction!(macd, m)?)?;
    m.add_function(wrap_pyfunction!(bbands, m)?)?;
    m.add_function(wrap_pyfunction!(adx, m)?)?;
    m.add_function(wrap_pyfunction!(swing_points_raw, m)?)?;
    m.add_function(wrap_pyfunction!(cci, m)?)?;
    m.add_function(wrap_pyfunction!(vwap, m)?)?;
    m.add_function(wrap_pyfunction!(obv, m)?)?;
    m.add_function(wrap_pyfunction!(klinger_vf, m)?)?;
    m.add_function(wrap_pyfunction!(cmf, m)?)?;
    m.add_function(wrap_pyfunction!(incremental_initialize, m)?)?;
    m.add_function(wrap_pyfunction!(incremental_step, m)?)?;
    m.add_function(wrap_pyfunction!(incremental_snapshot, m)?)?;
    m.add_function(wrap_pyfunction!(incremental_replay, m)?)?;
    Ok(())
}
