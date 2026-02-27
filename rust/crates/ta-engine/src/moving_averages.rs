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
