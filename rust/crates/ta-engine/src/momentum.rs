pub fn rsi(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || period == 0 || n < 2 {
        return out;
    }

    let mut avg_gain = 0.0;
    let mut avg_loss = 0.0;

    let seed = period.min(n - 1);
    for i in 1..=seed {
        let diff = values[i] - values[i - 1];
        if diff > 0.0 {
            avg_gain += diff;
        } else {
            avg_loss += -diff;
        }
    }

    avg_gain /= seed as f64;
    avg_loss /= seed as f64;

    if n <= period {
        return out;
    }

    // First RSI value appears at index = period
    out[period] = if avg_loss == 0.0 {
        if avg_gain > 0.0 {
            100.0
        } else {
            50.0
        }
    } else {
        let rs = avg_gain / avg_loss;
        100.0 - (100.0 / (1.0 + rs))
    };

    for i in (period + 1)..n {
        let diff = values[i] - values[i - 1];
        let gain = if diff > 0.0 { diff } else { 0.0 };
        let loss = if diff < 0.0 { -diff } else { 0.0 };

        avg_gain = (avg_gain * (period as f64 - 1.0) + gain) / period as f64;
        avg_loss = (avg_loss * (period as f64 - 1.0) + loss) / period as f64;

        out[i] = if avg_loss == 0.0 {
            if avg_gain > 0.0 {
                100.0
            } else {
                50.0
            }
        } else {
            let rs = avg_gain / avg_loss;
            100.0 - (100.0 / (1.0 + rs))
        };
    }

    out
}

pub fn stochastic_kd(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    k_period: usize,
    d_period: usize,
    smooth_period: usize,
) -> (Vec<f64>, Vec<f64>) {
    let n = close.len();
    let mut k = vec![f64::NAN; n];
    let mut d = vec![f64::NAN; n];
    if n == 0 || k_period == 0 || d_period == 0 || high.len() != n || low.len() != n {
        return (k, d);
    }

    for i in 0..n {
        if i + 1 < k_period {
            continue;
        }
        let start = i + 1 - k_period;
        let mut hh = high[start];
        let mut ll = low[start];
        for j in (start + 1)..=i {
            if high[j] > hh {
                hh = high[j];
            }
            if low[j] < ll {
                ll = low[j];
            }
        }
        let denom = hh - ll;
        let k_val = if denom == 0.0 {
            50.0
        } else {
            100.0 * (close[i] - ll) / denom
        };
        k[i] = k_val;
    }

    // Apply smoothing to %K if smooth_period > 1
    let k_smoothed = if smooth_period > 1 {
        crate::rolling::rolling_mean(&k, smooth_period)
    } else {
        k
    };

    for i in 0..n {
        if i + 1 < d_period {
            continue;
        }
        let start = i + 1 - d_period;
        let mut sum = 0.0;
        let mut valid = true;
        for value in &k_smoothed[start..=i] {
            if value.is_nan() {
                valid = false;
                break;
            }
            sum += *value;
        }
        if valid {
            d[i] = sum / d_period as f64;
        }
    }

    (k_smoothed, d)
}
