use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, OnceLock};

pub type DatasetId = u64;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct DatasetPartitionKey {
    pub symbol: String,
    pub timeframe: String,
    pub source: String,
}

#[derive(Debug, Clone, PartialEq)]
pub struct OhlcvColumns {
    pub timestamps: Vec<i64>,
    pub open: Vec<f64>,
    pub high: Vec<f64>,
    pub low: Vec<f64>,
    pub close: Vec<f64>,
    pub volume: Vec<f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct SeriesColumn {
    pub timestamps: Vec<i64>,
    pub values: Vec<f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct DatasetPartition {
    pub ohlcv: Option<OhlcvColumns>,
    pub series: HashMap<String, SeriesColumn>,
}

impl DatasetPartition {
    fn new() -> Self {
        Self {
            ohlcv: None,
            series: HashMap::new(),
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct DatasetRecord {
    pub id: DatasetId,
    pub partitions: HashMap<DatasetPartitionKey, DatasetPartition>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DatasetInfo {
    pub id: DatasetId,
    pub partition_count: usize,
    pub ohlcv_row_count: usize,
    pub series_row_count: usize,
    pub series_count: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DatasetRegistryError {
    UnknownDatasetId(DatasetId),
    LengthMismatch {
        field: &'static str,
        expected: usize,
        got: usize,
    },
    NonMonotonicTimestamps {
        field: &'static str,
    },
    EmptyField {
        field: &'static str,
    },
}

impl std::fmt::Display for DatasetRegistryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::UnknownDatasetId(id) => write!(f, "unknown dataset id: {id}"),
            Self::LengthMismatch {
                field,
                expected,
                got,
            } => write!(
                f,
                "length mismatch for {field}: expected {expected}, got {got}"
            ),
            Self::NonMonotonicTimestamps { field } => {
                write!(f, "timestamps must be non-decreasing for {field}")
            }
            Self::EmptyField { field } => write!(f, "empty field not allowed: {field}"),
        }
    }
}

impl std::error::Error for DatasetRegistryError {}

static NEXT_DATASET_ID: AtomicU64 = AtomicU64::new(1);
static DATASET_REGISTRY: OnceLock<Mutex<HashMap<DatasetId, DatasetRecord>>> = OnceLock::new();

fn registry() -> &'static Mutex<HashMap<DatasetId, DatasetRecord>> {
    DATASET_REGISTRY.get_or_init(|| Mutex::new(HashMap::new()))
}

pub fn create_dataset() -> DatasetId {
    let id = NEXT_DATASET_ID.fetch_add(1, Ordering::Relaxed);
    let mut map = registry().lock().expect("dataset registry lock poisoned");
    map.insert(
        id,
        DatasetRecord {
            id,
            partitions: HashMap::new(),
        },
    );
    id
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

pub fn dataset_info(id: DatasetId) -> Result<DatasetInfo, DatasetRegistryError> {
    let map = registry().lock().expect("dataset registry lock poisoned");
    let record = map
        .get(&id)
        .ok_or(DatasetRegistryError::UnknownDatasetId(id))?;

    let mut ohlcv_rows = 0_usize;
    let mut series_rows = 0_usize;
    let mut series_count = 0_usize;
    for partition in record.partitions.values() {
        if let Some(ohlcv) = &partition.ohlcv {
            ohlcv_rows += ohlcv.timestamps.len();
        }
        for series in partition.series.values() {
            series_rows += series.timestamps.len();
            series_count += 1;
        }
    }

    Ok(DatasetInfo {
        id,
        partition_count: record.partitions.len(),
        ohlcv_row_count: ohlcv_rows,
        series_row_count: series_rows,
        series_count,
    })
}

pub fn append_ohlcv(
    id: DatasetId,
    key: DatasetPartitionKey,
    timestamps: &[i64],
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    volume: &[f64],
) -> Result<usize, DatasetRegistryError> {
    if key.source.trim().is_empty() {
        return Err(DatasetRegistryError::EmptyField { field: "source" });
    }
    if key.symbol.trim().is_empty() {
        return Err(DatasetRegistryError::EmptyField { field: "symbol" });
    }
    if key.timeframe.trim().is_empty() {
        return Err(DatasetRegistryError::EmptyField { field: "timeframe" });
    }

    let expected = timestamps.len();
    ensure_same_len("open", expected, open.len())?;
    ensure_same_len("high", expected, high.len())?;
    ensure_same_len("low", expected, low.len())?;
    ensure_same_len("close", expected, close.len())?;
    ensure_same_len("volume", expected, volume.len())?;
    ensure_strictly_increasing_timestamps("timestamps", timestamps)?;

    let mut map = registry().lock().expect("dataset registry lock poisoned");
    let record = map
        .get_mut(&id)
        .ok_or(DatasetRegistryError::UnknownDatasetId(id))?;
    let partition = record
        .partitions
        .entry(key)
        .or_insert_with(DatasetPartition::new);
    let columns = partition.ohlcv.get_or_insert_with(|| OhlcvColumns {
        timestamps: Vec::new(),
        open: Vec::new(),
        high: Vec::new(),
        low: Vec::new(),
        close: Vec::new(),
        volume: Vec::new(),
    });

    if let (Some(last), Some(first)) = (columns.timestamps.last(), timestamps.first()) {
        if first < last {
            return Err(DatasetRegistryError::NonMonotonicTimestamps {
                field: "timestamps",
            });
        }
    }

    columns.timestamps.extend_from_slice(timestamps);
    columns.open.extend_from_slice(open);
    columns.high.extend_from_slice(high);
    columns.low.extend_from_slice(low);
    columns.close.extend_from_slice(close);
    columns.volume.extend_from_slice(volume);
    Ok(columns.timestamps.len())
}

pub fn append_series(
    id: DatasetId,
    key: DatasetPartitionKey,
    field: String,
    timestamps: &[i64],
    values: &[f64],
) -> Result<usize, DatasetRegistryError> {
    if key.source.trim().is_empty() {
        return Err(DatasetRegistryError::EmptyField { field: "source" });
    }
    if key.symbol.trim().is_empty() {
        return Err(DatasetRegistryError::EmptyField { field: "symbol" });
    }
    if key.timeframe.trim().is_empty() {
        return Err(DatasetRegistryError::EmptyField { field: "timeframe" });
    }
    if field.trim().is_empty() {
        return Err(DatasetRegistryError::EmptyField { field: "field" });
    }

    let expected = timestamps.len();
    ensure_same_len("values", expected, values.len())?;
    ensure_strictly_increasing_timestamps("timestamps", timestamps)?;

    let mut map = registry().lock().expect("dataset registry lock poisoned");
    let record = map
        .get_mut(&id)
        .ok_or(DatasetRegistryError::UnknownDatasetId(id))?;
    let partition = record
        .partitions
        .entry(key)
        .or_insert_with(DatasetPartition::new);

    let series = partition
        .series
        .entry(field)
        .or_insert_with(|| SeriesColumn {
            timestamps: Vec::new(),
            values: Vec::new(),
        });

    if let (Some(last), Some(first)) = (series.timestamps.last(), timestamps.first()) {
        if first < last {
            return Err(DatasetRegistryError::NonMonotonicTimestamps {
                field: "timestamps",
            });
        }
    }

    series.timestamps.extend_from_slice(timestamps);
    series.values.extend_from_slice(values);
    Ok(series.timestamps.len())
}

pub fn get_dataset(id: DatasetId) -> Result<DatasetRecord, DatasetRegistryError> {
    let map = registry().lock().expect("dataset registry lock poisoned");
    map.get(&id)
        .cloned()
        .ok_or(DatasetRegistryError::UnknownDatasetId(id))
}

fn ensure_same_len(
    field: &'static str,
    expected: usize,
    got: usize,
) -> Result<(), DatasetRegistryError> {
    if expected == got {
        Ok(())
    } else {
        Err(DatasetRegistryError::LengthMismatch {
            field,
            expected,
            got,
        })
    }
}

fn ensure_strictly_increasing_timestamps(
    field: &'static str,
    timestamps: &[i64],
) -> Result<(), DatasetRegistryError> {
    if timestamps
        .windows(2)
        .all(|w| matches!(w, [a, b] if b >= a))
    {
        Ok(())
    } else {
        Err(DatasetRegistryError::NonMonotonicTimestamps { field })
    }
}
