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

pub fn cci(high: &[f64], low: &[f64], close: &[f64], period: usize) -> Vec<f64> {
    let n = close.len();
    if n == 0 || period == 0 {
        return vec![f64::NAN; n];
    }

    let mut tp = vec![0.0; n];
    for i in 0..n {
        tp[i] = (high[i] + low[i] + close[i]) / 3.0;
    }

    let sma = crate::rolling::rolling_mean(&tp, period);
    let mut out = vec![f64::NAN; n];

    for i in 0..n {
        if i + 1 < period {
            continue;
        }

        let mut mean_deviation = 0.0;
        let start = i + 1 - period;
        let current_sma = sma[i];

        for j in start..=i {
            mean_deviation += (tp[j] - current_sma).abs();
        }
        mean_deviation /= period as f64;

        if mean_deviation == 0.0 {
            out[i] = 0.0;
        } else {
            out[i] = (tp[i] - current_sma) / (0.015 * mean_deviation);
        }
    }

    out
}

pub fn roc(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if period == 0 || n == 0 {
        return out;
    }

    for i in period..n {
        let prev = values[i - period];
        if prev == 0.0 || prev.is_nan() || values[i].is_nan() {
            out[i] = f64::NAN;
        } else {
            out[i] = ((values[i] - prev) / prev) * 100.0;
        }
    }
    out
}

pub fn williams_r(high: &[f64], low: &[f64], close: &[f64], period: usize) -> Vec<f64> {
    let n = close.len();
    let mut out = vec![f64::NAN; n];
    if period == 0 || high.len() != n || low.len() != n || n == 0 {
        return out;
    }

    for i in 0..n {
        if i + 1 < period {
            continue;
        }
        let start = i + 1 - period;
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
        let range = hh - ll;
        if range == 0.0 {
            out[i] = 0.0;
        } else {
            out[i] = ((hh - close[i]) / range) * -100.0;
        }
    }
    out
}

pub fn cmo(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if period == 0 || n < 2 {
        return out;
    }

    let mut gains = vec![0.0; n];
    let mut losses = vec![0.0; n];
    for i in 1..n {
        let diff = values[i] - values[i - 1];
        if diff > 0.0 {
            gains[i] = diff;
        } else {
            losses[i] = -diff;
        }
    }

    let sum_gains = crate::rolling::rolling_sum(&gains, period);
    let sum_losses = crate::rolling::rolling_sum(&losses, period);

    for i in 0..n {
        let sg = sum_gains[i];
        let sl = sum_losses[i];
        if sg.is_nan() || sl.is_nan() {
            continue;
        }
        let denom = sg + sl;
        out[i] = if denom == 0.0 {
            0.0
        } else {
            100.0 * (sg - sl) / denom
        };
    }

    out
}

pub fn ao(high: &[f64], low: &[f64], fast_period: usize, slow_period: usize) -> Vec<f64> {
    let n = high.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || low.len() != n || fast_period == 0 || slow_period == 0 {
        return out;
    }

    let mut median = vec![0.0; n];
    for i in 0..n {
        median[i] = (high[i] + low[i]) / 2.0;
    }

    let fast = crate::rolling::rolling_mean(&median, fast_period);
    let slow = crate::rolling::rolling_mean(&median, slow_period);

    for i in 0..n {
        if fast[i].is_nan() || slow[i].is_nan() {
            continue;
        }
        out[i] = fast[i] - slow[i];
    }
    out
}

pub fn coppock(values: &[f64], wma_period: usize, fast_roc: usize, slow_roc: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || wma_period == 0 || fast_roc == 0 || slow_roc == 0 {
        return out;
    }

    let roc_fast = roc(values, fast_roc);
    let roc_slow = roc(values, slow_roc);
    let mut sum = vec![f64::NAN; n];
    for i in 0..n {
        if !roc_fast[i].is_nan() && !roc_slow[i].is_nan() {
            sum[i] = roc_fast[i] + roc_slow[i];
        }
    }
    crate::moving_averages::wma(&sum, wma_period)
}

pub fn mfi(high: &[f64], low: &[f64], close: &[f64], volume: &[f64], period: usize) -> Vec<f64> {
    let n = close.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || period == 0 || high.len() != n || low.len() != n || volume.len() != n {
        return out;
    }

    let mut tp = vec![0.0; n];
    let mut rmf = vec![0.0; n];
    for i in 0..n {
        tp[i] = (high[i] + low[i] + close[i]) / 3.0;
        rmf[i] = tp[i] * volume[i];
    }

    let mut pos = vec![0.0; n];
    let mut neg = vec![0.0; n];
    for i in 1..n {
        if tp[i] > tp[i - 1] {
            pos[i] = rmf[i];
        } else if tp[i] < tp[i - 1] {
            neg[i] = rmf[i];
        }
    }

    let pos_sum = crate::rolling::rolling_sum(&pos, period);
    let neg_sum = crate::rolling::rolling_sum(&neg, period);
    for i in 0..n {
        if pos_sum[i].is_nan() || neg_sum[i].is_nan() {
            continue;
        }
        if neg_sum[i] == 0.0 {
            out[i] = 100.0;
        } else {
            let mfr = pos_sum[i] / neg_sum[i];
            out[i] = 100.0 - (100.0 / (1.0 + mfr));
        }
    }
    out
}

pub fn vortex(high: &[f64], low: &[f64], close: &[f64], period: usize) -> (Vec<f64>, Vec<f64>) {
    let n = close.len();
    let mut plus = vec![f64::NAN; n];
    let mut minus = vec![f64::NAN; n];
    if n == 0 || period == 0 || high.len() != n || low.len() != n {
        return (plus, minus);
    }

    let mut tr = vec![f64::NAN; n];
    let mut vm_plus = vec![f64::NAN; n];
    let mut vm_minus = vec![f64::NAN; n];

    for i in 1..n {
        vm_plus[i] = (high[i] - low[i - 1]).abs();
        vm_minus[i] = (low[i] - high[i - 1]).abs();

        let hl = high[i] - low[i];
        let hc = (high[i] - close[i - 1]).abs();
        let lc = (low[i] - close[i - 1]).abs();
        tr[i] = hl.max(hc).max(lc);
    }

    let tr_sum = crate::rolling::rolling_sum(&tr, period);
    let vp_sum = crate::rolling::rolling_sum(&vm_plus, period);
    let vm_sum = crate::rolling::rolling_sum(&vm_minus, period);

    for i in 0..n {
        if tr_sum[i].is_nan() || tr_sum[i] == 0.0 || vp_sum[i].is_nan() || vm_sum[i].is_nan() {
            continue;
        }
        plus[i] = vp_sum[i] / tr_sum[i];
        minus[i] = vm_sum[i] / tr_sum[i];
    }

    (plus, minus)
}
