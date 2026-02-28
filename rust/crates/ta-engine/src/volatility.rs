pub fn atr_from_tr(true_ranges: &[f64], period: usize) -> Vec<f64> {
    let n = true_ranges.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || period == 0 || n < period {
        return out;
    }

    let mut atr = true_ranges[..period].iter().sum::<f64>() / period as f64;
    out[period - 1] = atr;

    for i in period..n {
        atr = (atr * (period as f64 - 1.0) + true_ranges[i]) / period as f64;
        out[i] = atr;
    }

    out
}

pub fn atr(high: &[f64], low: &[f64], close: &[f64], period: usize) -> Vec<f64> {
    let n = close.len();
    if n == 0 {
        return Vec::new();
    }
    let mut tr = vec![0.0; n];
    for i in 1..n {
        let hl = high[i] - low[i];
        let hc = (high[i] - close[i - 1]).abs();
        let lc = (low[i] - close[i - 1]).abs();
        tr[i] = hl.max(hc).max(lc);
    }
    tr[0] = high[0] - low[0];
    atr_from_tr(&tr, period)
}

pub fn bbands(values: &[f64], period: usize, std_dev: f64) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let n = values.len();
    let mean = crate::rolling::rolling_mean(values, period);
    let std = crate::rolling::rolling_std(values, period);
    let mut upper = vec![f64::NAN; n];
    let mut lower = vec![f64::NAN; n];

    for i in 0..n {
        if !mean[i].is_nan() && !std[i].is_nan() {
            upper[i] = mean[i] + (std_dev * std[i]);
            lower[i] = mean[i] - (std_dev * std[i]);
        }
    }

    (upper, mean, lower)
}
