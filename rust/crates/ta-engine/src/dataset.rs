use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, OnceLock};

pub type DatasetId = u64;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DatasetHandle {
    pub id: DatasetId,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DatasetRegistryError {
    UnknownDatasetId(DatasetId),
}

impl std::fmt::Display for DatasetRegistryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::UnknownDatasetId(id) => write!(f, "unknown dataset id: {id}"),
        }
    }
}

impl std::error::Error for DatasetRegistryError {}

static NEXT_DATASET_ID: AtomicU64 = AtomicU64::new(1);
static DATASET_REGISTRY: OnceLock<Mutex<HashMap<DatasetId, DatasetHandle>>> = OnceLock::new();

fn registry() -> &'static Mutex<HashMap<DatasetId, DatasetHandle>> {
    DATASET_REGISTRY.get_or_init(|| Mutex::new(HashMap::new()))
}

pub fn create_dataset() -> DatasetId {
    let id = NEXT_DATASET_ID.fetch_add(1, Ordering::Relaxed);
    let mut map = registry().lock().expect("dataset registry lock poisoned");
    map.insert(id, DatasetHandle { id });
    id
}

pub fn get_dataset(id: DatasetId) -> Result<DatasetHandle, DatasetRegistryError> {
    let map = registry().lock().expect("dataset registry lock poisoned");
    map.get(&id)
        .copied()
        .ok_or(DatasetRegistryError::UnknownDatasetId(id))
}

pub fn drop_dataset(id: DatasetId) -> Result<(), DatasetRegistryError> {
    let mut map = registry().lock().expect("dataset registry lock poisoned");
    if map.remove(&id).is_some() {
        Ok(())
    } else {
        Err(DatasetRegistryError::UnknownDatasetId(id))
    }
}

pub fn dataset_exists(id: DatasetId) -> bool {
    let map = registry().lock().expect("dataset registry lock poisoned");
    map.contains_key(&id)
}

pub fn dataset_count() -> usize {
    let map = registry().lock().expect("dataset registry lock poisoned");
    map.len()
}
