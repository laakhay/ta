use thiserror::Error;

#[derive(Debug, Clone, Error, PartialEq, Eq)]
pub enum DatasetOpsError {
    #[error("timestamps and values must have identical lengths")]
    LengthMismatch,
    #[error("factor must be positive")]
    InvalidFactor,
    #[error("unsupported aggregation: {0}")]
    UnsupportedAggregation(String),
    #[error("unsupported sync fill mode: {0}")]
    UnsupportedFillMode(String),
}

pub fn downsample(
    timestamps: &[i64],
    values: &[f64],
    factor: usize,
    agg: &str,
) -> Result<(Vec<i64>, Vec<f64>), DatasetOpsError> {
    if timestamps.len() != values.len() {
        return Err(DatasetOpsError::LengthMismatch);
    }
    if factor == 0 {
        return Err(DatasetOpsError::InvalidFactor);
    }
    if factor <= 1 || timestamps.is_empty() {
        return Ok((timestamps.to_vec(), values.to_vec()));
    }

    let mut out_ts = Vec::with_capacity(timestamps.len().div_ceil(factor));
    let mut out_values = Vec::with_capacity(values.len().div_ceil(factor));

    let mut i = 0_usize;
    while i < timestamps.len() {
        let end = (i + factor).min(timestamps.len());
        out_ts.push(timestamps[end - 1]);
        let bucket = &values[i..end];
        let v = match agg {
            "first" => bucket[0],
            "last" => bucket[bucket.len() - 1],
            "mean" => bucket.iter().sum::<f64>() / bucket.len() as f64,
            "sum" => bucket.iter().sum(),
            "max" => bucket.iter().copied().fold(f64::NEG_INFINITY, f64::max),
            "min" => bucket.iter().copied().fold(f64::INFINITY, f64::min),
            other => return Err(DatasetOpsError::UnsupportedAggregation(other.to_string())),
        };
        out_values.push(v);
        i = end;
    }

    Ok((out_ts, out_values))
}

pub fn upsample_ffill(
    timestamps: &[i64],
    values: &[f64],
    factor: usize,
) -> Result<(Vec<i64>, Vec<f64>), DatasetOpsError> {
    if timestamps.len() != values.len() {
        return Err(DatasetOpsError::LengthMismatch);
    }
    if factor == 0 {
        return Err(DatasetOpsError::InvalidFactor);
    }
    if factor <= 1 || timestamps.is_empty() {
        return Ok((timestamps.to_vec(), values.to_vec()));
    }

    let mut out_ts = Vec::with_capacity((timestamps.len() - 1) * factor + 1);
    let mut out_values = Vec::with_capacity((values.len() - 1) * factor + 1);

    for idx in 0..timestamps.len() {
        out_ts.push(timestamps[idx]);
        out_values.push(values[idx]);
        if idx < timestamps.len() - 1 {
            for _ in 0..(factor - 1) {
                out_ts.push(timestamps[idx]);
                out_values.push(values[idx]);
            }
        }
    }
    Ok((out_ts, out_values))
}

pub fn sync_timeframe(
    source_timestamps: &[i64],
    source_values: &[f64],
    reference_timestamps: &[i64],
    fill: &str,
) -> Result<Vec<f64>, DatasetOpsError> {
    if source_timestamps.len() != source_values.len() {
        return Err(DatasetOpsError::LengthMismatch);
    }
    if reference_timestamps.is_empty() {
        return Ok(Vec::new());
    }
    if source_timestamps.is_empty() {
        return Ok(vec![0.0; reference_timestamps.len()]);
    }

    match fill {
        "ffill" => Ok(sync_ffill(
            source_timestamps,
            source_values,
            reference_timestamps,
        )),
        "linear" => Ok(sync_linear(
            source_timestamps,
            source_values,
            reference_timestamps,
        )),
        other => Err(DatasetOpsError::UnsupportedFillMode(other.to_string())),
    }
}

fn sync_ffill(
    source_timestamps: &[i64],
    source_values: &[f64],
    reference_timestamps: &[i64],
) -> Vec<f64> {
    let mut out = Vec::with_capacity(reference_timestamps.len());
    let mut pos = 0_usize;
    let mut last = source_values[0];
    for &ts in reference_timestamps {
        while pos < source_timestamps.len() && source_timestamps[pos] <= ts {
            last = source_values[pos];
            pos += 1;
        }
        out.push(last);
    }
    out
}

fn sync_linear(
    source_timestamps: &[i64],
    source_values: &[f64],
    reference_timestamps: &[i64],
) -> Vec<f64> {
    let mut out = Vec::with_capacity(reference_timestamps.len());
    for &ts in reference_timestamps {
        match source_timestamps.binary_search(&ts) {
            Ok(i) => out.push(source_values[i]),
            Err(i) => {
                if i == 0 {
                    out.push(source_values[0]);
                    continue;
                }
                if i >= source_timestamps.len() {
                    out.push(source_values[source_values.len() - 1]);
                    continue;
                }
                let t0 = source_timestamps[i - 1];
                let t1 = source_timestamps[i];
                let v0 = source_values[i - 1];
                let v1 = source_values[i];
                let denom = (t1 - t0) as f64;
                if denom == 0.0 {
                    out.push(v0);
                    continue;
                }
                let w = (ts - t0) as f64 / denom;
                out.push(v0 + (v1 - v0) * w);
            }
        }
    }
    out
}
