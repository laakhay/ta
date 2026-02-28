use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, OnceLock};

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::PyResult;
use ta_engine::incremental::backend::IncrementalBackend;
use ta_engine::incremental::contracts::RuntimeSnapshot;

static BACKEND_ID: AtomicU64 = AtomicU64::new(1);
static SNAPSHOT_ID: AtomicU64 = AtomicU64::new(1);
static BACKENDS: OnceLock<Mutex<HashMap<u64, IncrementalBackend>>> = OnceLock::new();
static SNAPSHOTS: OnceLock<Mutex<HashMap<u64, RuntimeSnapshot>>> = OnceLock::new();

pub(crate) fn next_backend_id() -> u64 {
    BACKEND_ID.fetch_add(1, Ordering::SeqCst)
}

pub(crate) fn next_snapshot_id() -> u64 {
    SNAPSHOT_ID.fetch_add(1, Ordering::SeqCst)
}

pub(crate) fn with_backends_mut<T>(
    f: impl FnOnce(&mut HashMap<u64, IncrementalBackend>) -> T,
) -> PyResult<T> {
    let mut map = BACKENDS
        .get_or_init(|| Mutex::new(HashMap::new()))
        .lock()
        .map_err(|_| PyRuntimeError::new_err("failed to lock backend registry"))?;
    Ok(f(&mut map))
}

pub(crate) fn with_snapshots_mut<T>(
    f: impl FnOnce(&mut HashMap<u64, RuntimeSnapshot>) -> T,
) -> PyResult<T> {
    let mut map = SNAPSHOTS
        .get_or_init(|| Mutex::new(HashMap::new()))
        .lock()
        .map_err(|_| PyRuntimeError::new_err("failed to lock snapshot registry"))?;
    Ok(f(&mut map))
}

pub(crate) fn with_snapshots<T>(
    f: impl FnOnce(&HashMap<u64, RuntimeSnapshot>) -> T,
) -> PyResult<T> {
    let map = SNAPSHOTS
        .get_or_init(|| Mutex::new(HashMap::new()))
        .lock()
        .map_err(|_| PyRuntimeError::new_err("failed to lock snapshot registry"))?;
    Ok(f(&map))
}
