use std::collections::{BTreeMap, HashMap};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, OnceLock};

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use ta_engine::dataset::{self, DatasetPartitionKey, DatasetRegistryError};
use ta_engine::dataset_ops::DatasetOpsError;
use ta_engine::incremental::backend::{
    self, ExecutePlanError, ExecutePlanPayload, IncrementalBackend, KernelStepRequest,
};
use ta_engine::incremental::contracts::{IncrementalValue, RuntimeSnapshot};
use ta_engine::incremental::kernel_registry::KernelId;

static BACKEND_ID: AtomicU64 = AtomicU64::new(1);
static SNAPSHOT_ID: AtomicU64 = AtomicU64::new(1);
static BACKENDS: OnceLock<Mutex<HashMap<u64, IncrementalBackend>>> = OnceLock::new();
static SNAPSHOTS: OnceLock<Mutex<HashMap<u64, RuntimeSnapshot>>> = OnceLock::new();

type IchimokuTuple = (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>);

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

#[pyfunction]
fn dataset_create() -> u64 {
    dataset::create_dataset()
}

#[pyfunction]
fn dataset_drop(dataset_id: u64) -> PyResult<()> {
    dataset::drop_dataset(dataset_id).map_err(map_dataset_error)
}

#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn dataset_append_ohlcv(
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
fn dataset_append_series(
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
fn dataset_info(py: Python<'_>, dataset_id: u64) -> PyResult<PyObject> {
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
fn series_downsample(
    timestamps: Vec<i64>,
    values: Vec<f64>,
    factor: usize,
    agg: String,
) -> PyResult<(Vec<i64>, Vec<f64>)> {
    ta_engine::dataset_ops::downsample(&timestamps, &values, factor, &agg).map_err(map_dataset_ops_error)
}

#[pyfunction]
fn series_upsample_ffill(
    timestamps: Vec<i64>,
    values: Vec<f64>,
    factor: usize,
) -> PyResult<(Vec<i64>, Vec<f64>)> {
    ta_engine::dataset_ops::upsample_ffill(&timestamps, &values, factor).map_err(map_dataset_ops_error)
}

#[pyfunction]
fn series_sync_timeframe(
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
fn indicator_catalog(py: Python<'_>) -> PyResult<PyObject> {
    let py_list = PyList::empty(py);
    for meta in ta_engine::metadata::indicator_catalog() {
        py_list.append(indicator_meta_to_pydict(py, meta)?)?;
    }
    Ok(py_list.into_any().unbind())
}

#[pyfunction]
fn indicator_meta(py: Python<'_>, id: String) -> PyResult<PyObject> {
    let meta = ta_engine::metadata::find_indicator_meta(&id).ok_or_else(|| {
        pyo3::exceptions::PyKeyError::new_err(format!(
            "indicator metadata not found for id/alias '{id}'"
        ))
    })?;
    indicator_meta_to_pydict(py, meta)
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
fn roc(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::momentum::roc(&values, period))
}

#[pyfunction]
fn cmo(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::momentum::cmo(&values, period))
}

#[pyfunction]
fn ao(high: Vec<f64>, low: Vec<f64>, fast_period: usize, slow_period: usize) -> PyResult<Vec<f64>> {
    validate_period(fast_period)?;
    validate_period(slow_period)?;
    Ok(ta_engine::momentum::ao(
        &high,
        &low,
        fast_period,
        slow_period,
    ))
}

#[pyfunction]
fn coppock(
    values: Vec<f64>,
    wma_period: usize,
    fast_roc: usize,
    slow_roc: usize,
) -> PyResult<Vec<f64>> {
    validate_period(wma_period)?;
    validate_period(fast_roc)?;
    validate_period(slow_roc)?;
    Ok(ta_engine::momentum::coppock(
        &values, wma_period, fast_roc, slow_roc,
    ))
}

#[pyfunction]
fn mfi(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    period: usize,
) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::momentum::mfi(
        &high, &low, &close, &volume, period,
    ))
}

#[pyfunction]
fn vortex(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::momentum::vortex(&high, &low, &close, period))
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
fn donchian(
    high: Vec<f64>,
    low: Vec<f64>,
    period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::volatility::donchian(&high, &low, period))
}

#[pyfunction]
fn keltner(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    ema_period: usize,
    atr_period: usize,
    multiplier: f64,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_period(ema_period)?;
    validate_period(atr_period)?;
    Ok(ta_engine::volatility::keltner(
        &high, &low, &close, ema_period, atr_period, multiplier,
    ))
}

#[pyfunction]
fn ichimoku(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    tenkan_period: usize,
    kijun_period: usize,
    span_b_period: usize,
    displacement: usize,
) -> PyResult<IchimokuTuple> {
    validate_period(tenkan_period)?;
    validate_period(kijun_period)?;
    validate_period(span_b_period)?;
    validate_period(displacement)?;
    Ok(ta_engine::trend::ichimoku(
        &high,
        &low,
        &close,
        tenkan_period,
        kijun_period,
        span_b_period,
        displacement,
    ))
}

#[pyfunction]
fn fisher(high: Vec<f64>, low: Vec<f64>, period: usize) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::trend::fisher(&high, &low, period))
}

#[pyfunction]
fn psar(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    af_start: f64,
    af_increment: f64,
    af_max: f64,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    Ok(ta_engine::trend::psar(
        &high,
        &low,
        &close,
        af_start,
        af_increment,
        af_max,
    ))
}

#[pyfunction]
fn supertrend(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
    multiplier: f64,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::trend::supertrend(
        &high, &low, &close, period, multiplier,
    ))
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
fn elder_ray(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::trend::elder_ray(&high, &low, &close, period))
}

#[pyfunction]
fn williams_r(high: Vec<f64>, low: Vec<f64>, close: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::momentum::williams_r(&high, &low, &close, period))
}

#[pyfunction]
fn crossup(a: Vec<f64>, b: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::crossup(&a, &b))
}

#[pyfunction]
fn crossdown(a: Vec<f64>, b: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::crossdown(&a, &b))
}

#[pyfunction]
fn cross(a: Vec<f64>, b: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::cross(&a, &b))
}

#[pyfunction]
fn rising(a: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::rising(&a))
}

#[pyfunction]
fn falling(a: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::falling(&a))
}

#[pyfunction]
fn rising_pct(a: Vec<f64>, pct: f64) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::rising_pct(&a, pct))
}

#[pyfunction]
fn falling_pct(a: Vec<f64>, pct: f64) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::falling_pct(&a, pct))
}

#[pyfunction]
fn in_channel(price: Vec<f64>, upper: Vec<f64>, lower: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::in_channel(&price, &upper, &lower))
}

#[pyfunction]
fn out_channel(price: Vec<f64>, upper: Vec<f64>, lower: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::out_channel(&price, &upper, &lower))
}

#[pyfunction]
fn enter_channel(price: Vec<f64>, upper: Vec<f64>, lower: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::enter_channel(&price, &upper, &lower))
}

#[pyfunction]
fn exit_channel(price: Vec<f64>, upper: Vec<f64>, lower: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::exit_channel(&price, &upper, &lower))
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
fn klinger(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(fast_period)?;
    validate_period(slow_period)?;
    validate_period(signal_period)?;
    Ok(ta_engine::volume::klinger(
        &high,
        &low,
        &close,
        &volume,
        fast_period,
        slow_period,
        signal_period,
    ))
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

#[pyfunction]
fn execute_plan(
    py: Python<'_>,
    dataset_id: u64,
    symbol: String,
    timeframe: String,
    source: String,
    requests: &Bound<'_, PyList>,
) -> PyResult<PyObject> {
    let parsed_requests = parse_requests(requests)?;
    let payload = ExecutePlanPayload {
        dataset_id,
        partition_key: DatasetPartitionKey {
            symbol,
            timeframe,
            source,
        },
        requests: parsed_requests,
    };
    let out = backend::execute_plan_payload(&payload).map_err(map_execute_plan_error)?;
    incremental_series_map_to_pydict(py, &out)
}

#[pyfunction]
fn execute_plan_payload(py: Python<'_>, payload: &Bound<'_, PyDict>) -> PyResult<PyObject> {
    let dataset_id: u64 = payload
        .get_item("dataset_id")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing dataset_id"))?
        .extract()?;
    let partition = payload
        .get_item("partition")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing partition"))?
        .downcast_into::<PyDict>()?;
    let symbol: String = partition
        .get_item("symbol")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing partition.symbol"))?
        .extract()?;
    let timeframe: String = partition
        .get_item("timeframe")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing partition.timeframe"))?
        .extract()?;
    let source: String = partition
        .get_item("source")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing partition.source"))?
        .extract()?;
    let requests = payload
        .get_item("requests")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing requests"))?
        .downcast_into::<PyList>()?;

    let parsed_requests = parse_requests(&requests)?;
    let payload = ExecutePlanPayload {
        dataset_id,
        partition_key: DatasetPartitionKey {
            symbol,
            timeframe,
            source,
        },
        requests: parsed_requests,
    };
    let out = backend::execute_plan_payload(&payload).map_err(map_execute_plan_error)?;
    incremental_series_map_to_pydict(py, &out)
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

fn incremental_series_map_to_pydict(
    py: Python<'_>,
    values: &BTreeMap<u32, Vec<IncrementalValue>>,
) -> PyResult<PyObject> {
    let d = PyDict::new(py);
    for (k, series) in values {
        let py_list = PyList::empty(py);
        for v in series {
            match v {
                IncrementalValue::Number(n) => py_list.append(*n)?,
                IncrementalValue::Bool(b) => py_list.append(*b)?,
                IncrementalValue::Text(s) => py_list.append(s)?,
                IncrementalValue::Null => py_list.append(py.None())?,
            }
        }
        d.set_item(k, py_list)?;
    }
    Ok(d.into_any().unbind())
}

fn map_execute_plan_error(err: ExecutePlanError) -> PyErr {
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
    }
}

fn map_dataset_ops_error(err: DatasetOpsError) -> PyErr {
    match err {
        DatasetOpsError::LengthMismatch => {
            pyo3::exceptions::PyValueError::new_err("timestamps and values must have identical lengths")
        }
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

fn indicator_meta_to_pydict(
    py: Python<'_>,
    meta: &ta_engine::metadata::IndicatorMeta,
) -> PyResult<PyObject> {
    let d = PyDict::new(py);
    d.set_item("id", meta.id)?;
    d.set_item("display_name", meta.display_name)?;
    d.set_item("category", meta.category)?;
    d.set_item("runtime_binding", meta.runtime_binding)?;

    let aliases = PyList::empty(py);
    for alias in meta.aliases {
        aliases.append(alias)?;
    }
    d.set_item("aliases", aliases)?;

    let param_aliases = PyDict::new(py);
    for alias in meta.param_aliases {
        param_aliases.set_item(alias.alias, alias.target)?;
    }
    d.set_item("param_aliases", param_aliases)?;

    let params = PyList::empty(py);
    for param in meta.params {
        let p = PyDict::new(py);
        p.set_item("name", param.name)?;
        let kind = match param.kind {
            ta_engine::metadata::IndicatorParamKind::Integer => "int",
            ta_engine::metadata::IndicatorParamKind::Float => "float",
            ta_engine::metadata::IndicatorParamKind::Boolean => "bool",
            ta_engine::metadata::IndicatorParamKind::String => "string",
        };
        p.set_item("kind", kind)?;
        p.set_item("required", param.required)?;
        p.set_item("default", param.default)?;
        p.set_item("description", param.description)?;
        p.set_item("min", param.min)?;
        p.set_item("max", param.max)?;
        params.append(p)?;
    }
    d.set_item("params", params)?;

    let outputs = PyList::empty(py);
    for output in meta.outputs {
        let o = PyDict::new(py);
        o.set_item("name", output.name)?;
        o.set_item("kind", output.kind)?;
        o.set_item("description", output.description)?;
        outputs.append(o)?;
    }
    d.set_item("outputs", outputs)?;

    let semantics = PyDict::new(py);
    let required_fields = PyList::empty(py);
    for field in meta.semantics.required_fields {
        required_fields.append(field)?;
    }
    semantics.set_item("required_fields", required_fields)?;

    let optional_fields = PyList::empty(py);
    for field in meta.semantics.optional_fields {
        optional_fields.append(field)?;
    }
    semantics.set_item("optional_fields", optional_fields)?;

    let lookback_params = PyList::empty(py);
    for param in meta.semantics.lookback_params {
        lookback_params.append(param)?;
    }
    semantics.set_item("lookback_params", lookback_params)?;
    semantics.set_item("default_lookback", meta.semantics.default_lookback)?;
    semantics.set_item("warmup_policy", meta.semantics.warmup_policy)?;
    d.set_item("semantics", semantics)?;

    Ok(d.into_any().unbind())
}

fn map_dataset_error(err: DatasetRegistryError) -> PyErr {
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

#[pymodule]
fn ta_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(engine_version, m)?)?;
    m.add_function(wrap_pyfunction!(dataset_create, m)?)?;
    m.add_function(wrap_pyfunction!(dataset_drop, m)?)?;
    m.add_function(wrap_pyfunction!(dataset_append_ohlcv, m)?)?;
    m.add_function(wrap_pyfunction!(dataset_append_series, m)?)?;
    m.add_function(wrap_pyfunction!(dataset_info, m)?)?;
    m.add_function(wrap_pyfunction!(series_downsample, m)?)?;
    m.add_function(wrap_pyfunction!(series_upsample_ffill, m)?)?;
    m.add_function(wrap_pyfunction!(series_sync_timeframe, m)?)?;
    m.add_function(wrap_pyfunction!(indicator_catalog, m)?)?;
    m.add_function(wrap_pyfunction!(indicator_meta, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_sum, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_mean, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_std, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_min, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_max, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_ema, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_rma, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_wma, m)?)?;
    m.add_function(wrap_pyfunction!(rsi, m)?)?;
    m.add_function(wrap_pyfunction!(roc, m)?)?;
    m.add_function(wrap_pyfunction!(cmo, m)?)?;
    m.add_function(wrap_pyfunction!(ao, m)?)?;
    m.add_function(wrap_pyfunction!(coppock, m)?)?;
    m.add_function(wrap_pyfunction!(mfi, m)?)?;
    m.add_function(wrap_pyfunction!(vortex, m)?)?;
    m.add_function(wrap_pyfunction!(atr, m)?)?;
    m.add_function(wrap_pyfunction!(atr_from_tr, m)?)?;
    m.add_function(wrap_pyfunction!(stochastic_kd, m)?)?;
    m.add_function(wrap_pyfunction!(macd, m)?)?;
    m.add_function(wrap_pyfunction!(bbands, m)?)?;
    m.add_function(wrap_pyfunction!(donchian, m)?)?;
    m.add_function(wrap_pyfunction!(keltner, m)?)?;
    m.add_function(wrap_pyfunction!(ichimoku, m)?)?;
    m.add_function(wrap_pyfunction!(fisher, m)?)?;
    m.add_function(wrap_pyfunction!(psar, m)?)?;
    m.add_function(wrap_pyfunction!(supertrend, m)?)?;
    m.add_function(wrap_pyfunction!(adx, m)?)?;
    m.add_function(wrap_pyfunction!(swing_points_raw, m)?)?;
    m.add_function(wrap_pyfunction!(cci, m)?)?;
    m.add_function(wrap_pyfunction!(williams_r, m)?)?;
    m.add_function(wrap_pyfunction!(elder_ray, m)?)?;
    m.add_function(wrap_pyfunction!(crossup, m)?)?;
    m.add_function(wrap_pyfunction!(crossdown, m)?)?;
    m.add_function(wrap_pyfunction!(cross, m)?)?;
    m.add_function(wrap_pyfunction!(rising, m)?)?;
    m.add_function(wrap_pyfunction!(falling, m)?)?;
    m.add_function(wrap_pyfunction!(rising_pct, m)?)?;
    m.add_function(wrap_pyfunction!(falling_pct, m)?)?;
    m.add_function(wrap_pyfunction!(in_channel, m)?)?;
    m.add_function(wrap_pyfunction!(out_channel, m)?)?;
    m.add_function(wrap_pyfunction!(enter_channel, m)?)?;
    m.add_function(wrap_pyfunction!(exit_channel, m)?)?;
    m.add_function(wrap_pyfunction!(vwap, m)?)?;
    m.add_function(wrap_pyfunction!(obv, m)?)?;
    m.add_function(wrap_pyfunction!(klinger_vf, m)?)?;
    m.add_function(wrap_pyfunction!(klinger, m)?)?;
    m.add_function(wrap_pyfunction!(cmf, m)?)?;
    m.add_function(wrap_pyfunction!(incremental_initialize, m)?)?;
    m.add_function(wrap_pyfunction!(incremental_step, m)?)?;
    m.add_function(wrap_pyfunction!(incremental_snapshot, m)?)?;
    m.add_function(wrap_pyfunction!(incremental_replay, m)?)?;
    m.add_function(wrap_pyfunction!(execute_plan, m)?)?;
    m.add_function(wrap_pyfunction!(execute_plan_payload, m)?)?;
    Ok(())
}
