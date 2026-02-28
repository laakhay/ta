use crate::rolling;

pub fn ema(values: &[f64], period: usize) -> Vec<f64> {
    rolling::ema(values, period)
}

pub fn rma(values: &[f64], period: usize) -> Vec<f64> {
    rolling::rma(values, period)
}

pub fn wma(values: &[f64], period: usize) -> Vec<f64> {
    rolling::wma(values, period)
}

pub fn hma(values: &[f64], period: usize) -> Vec<f64> {
    if period == 0 {
        return vec![f64::NAN; values.len()];
    }
    let half = (period / 2).max(1);
    let sqrt_n = ((period as f64).sqrt() as usize).max(1);

    let wma_half = rolling::wma(values, half);
    let wma_full = rolling::wma(values, period);
    let raw: Vec<f64> = wma_half
        .iter()
        .zip(wma_full.iter())
        .map(|(a, b)| (2.0 * *a) - *b)
        .collect();
    rolling::wma(&raw, sqrt_n)
}
