use crate::moving_averages::ema;

pub fn macd(
    values: &[f64],
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let fast_ema = ema(values, fast_period);
    let slow_ema = ema(values, slow_period);
    let n = values.len();
    let mut macd_line = vec![f64::NAN; n];

    for i in 0..n {
        if !fast_ema[i].is_nan() && !slow_ema[i].is_nan() {
            macd_line[i] = fast_ema[i] - slow_ema[i];
        }
    }

    // Signal line is EMA of MACD line.
    // We need to handle the leading NaNs carefully or just use the whole series.
    // The standard way is to calculate EMA on the available MACD values.
    let signal_line = ema(&macd_line, signal_period);
    let mut histogram = vec![f64::NAN; n];

    for i in 0..n {
        if !macd_line[i].is_nan() && !signal_line[i].is_nan() {
            histogram[i] = macd_line[i] - signal_line[i];
        }
    }

    (macd_line, signal_line, histogram)
}

pub fn adx(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let n = close.len();
    if n < 2 || period == 0 {
        return (vec![f64::NAN; n], vec![f64::NAN; n], vec![f64::NAN; n]);
    }

    let mut plus_dm = vec![0.0; n];
    let mut minus_dm = vec![0.0; n];
    let mut tr = vec![0.0; n];

    for i in 1..n {
        let up = high[i] - high[i - 1];
        let down = low[i - 1] - low[i];

        plus_dm[i] = if up > down && up > 0.0 { up } else { 0.0 };
        minus_dm[i] = if down > up && down > 0.0 { down } else { 0.0 };

        let hl = high[i] - low[i];
        let hc = (high[i] - close[i - 1]).abs();
        let lc = (low[i] - close[i - 1]).abs();
        tr[i] = hl.max(hc).max(lc);
    }

    let smooth_tr = wilder_smooth(&tr, period);
    let smooth_plus_dm = wilder_smooth(&plus_dm, period);
    let smooth_minus_dm = wilder_smooth(&minus_dm, period);

    let mut plus_di = vec![f64::NAN; n];
    let mut minus_di = vec![f64::NAN; n];
    let mut dx = vec![f64::NAN; n];

    for i in 0..n {
        let tr_val = smooth_tr[i];
        if tr_val > 0.0 {
            let pdi = 100.0 * smooth_plus_dm[i] / tr_val;
            let mdi = 100.0 * smooth_minus_dm[i] / tr_val;
            plus_di[i] = pdi;
            minus_di[i] = mdi;
            let sum = pdi + mdi;
            dx[i] = if sum > 0.0 {
                100.0 * (pdi - mdi).abs() / sum
            } else {
                0.0
            };
        }
    }

    // ADX is the EMA (or Wilder smoothing) of DX
    // Note: Wilder smoothing is equivalent to RMA (Relative Moving Average)
    let adx = wilder_smooth_non_negative(&dx, period);

    (adx, plus_di, minus_di)
}

fn wilder_smooth(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if n < period {
        return out;
    }

    let mut sum = values[..period].iter().sum::<f64>();
    out[period - 1] = sum;

    for i in period..n {
        sum = sum - (sum / period as f64) + values[i];
        out[i] = sum;
    }
    out
}

fn wilder_smooth_non_negative(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];

    // Find first non-NaN
    let first = values.iter().position(|v| !v.is_nan());
    let Some(start) = first else {
        return out;
    };

    if n - start < period {
        return out;
    }

    let mut sum = values[start..start + period].iter().sum::<f64>();
    out[start + period - 1] = sum / period as f64;

    for i in (start + period)..n {
        let prev = out[i - 1];
        out[i] = (prev * (period as f64 - 1.0) + values[i]) / period as f64;
    }
    out
}
