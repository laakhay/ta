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
