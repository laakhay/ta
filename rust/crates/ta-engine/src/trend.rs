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

pub fn swing_points_raw(
    high: &[f64],
    low: &[f64],
    left: usize,
    right: usize,
    allow_equal_extremes: bool,
) -> (Vec<bool>, Vec<bool>) {
    let n = high.len();
    let mut raw_high = vec![false; n];
    let mut raw_low = vec![false; n];
    let mut have_high = false;

    if n <= left + right {
        return (raw_high, raw_low);
    }

    for i in left..(n - right) {
        let current_high = high[i];
        let current_low = low[i];

        let mut is_high = true;
        let mut count_high = 0;
        for j in (i - left)..(i + right + 1) {
            if high[j] > current_high {
                is_high = false;
                break;
            }
            if high[j] == current_high {
                count_high += 1;
            }
        }
        if is_high && (allow_equal_extremes || count_high == 1) {
            raw_high[i] = true;
            have_high = true;
        }

        if have_high {
            let mut is_low = true;
            let mut count_low = 0;
            for j in (i - left)..(i + right + 1) {
                if low[j] < current_low {
                    is_low = false;
                    break;
                }
                if low[j] == current_low {
                    count_low += 1;
                }
            }
            if is_low && (allow_equal_extremes || count_low == 1) {
                raw_low[i] = true;
            }
        }
    }

    let mut flags_high = vec![false; n];
    let mut flags_low = vec![false; n];

    for i in 0..n {
        let confirmed_idx = i + right;
        if confirmed_idx < n {
            if raw_high[i] {
                flags_high[confirmed_idx] = true;
            }
            if raw_low[i] {
                flags_low[confirmed_idx] = true;
            }
        }
    }

    (flags_high, flags_low)
}

pub fn elder_ray(high: &[f64], low: &[f64], close: &[f64], period: usize) -> (Vec<f64>, Vec<f64>) {
    let ema_vals = crate::moving_averages::ema(close, period);
    let n = close.len();
    let mut bull = vec![f64::NAN; n];
    let mut bear = vec![f64::NAN; n];
    for i in 0..n {
        if !ema_vals[i].is_nan() {
            bull[i] = high[i] - ema_vals[i];
            bear[i] = low[i] - ema_vals[i];
        }
    }
    (bull, bear)
}

pub fn ichimoku(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    tenkan_period: usize,
    kijun_period: usize,
    span_b_period: usize,
    displacement: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>) {
    let n = close.len();
    let mut empty = vec![f64::NAN; n];
    if n == 0
        || high.len() != n
        || low.len() != n
        || tenkan_period == 0
        || kijun_period == 0
        || span_b_period == 0
        || displacement == 0
    {
        return (
            empty.clone(),
            empty.clone(),
            empty.clone(),
            empty.clone(),
            empty,
        );
    }

    let tenkan_h = crate::rolling::rolling_max(high, tenkan_period);
    let tenkan_l = crate::rolling::rolling_min(low, tenkan_period);
    let kijun_h = crate::rolling::rolling_max(high, kijun_period);
    let kijun_l = crate::rolling::rolling_min(low, kijun_period);
    let span_b_h = crate::rolling::rolling_max(high, span_b_period);
    let span_b_l = crate::rolling::rolling_min(low, span_b_period);

    let mut tenkan = vec![f64::NAN; n];
    let mut kijun = vec![f64::NAN; n];
    let mut span_a = vec![f64::NAN; n];
    let mut span_b = vec![f64::NAN; n];
    let mut chikou = vec![f64::NAN; n];

    for i in 0..n {
        if !tenkan_h[i].is_nan() && !tenkan_l[i].is_nan() {
            tenkan[i] = (tenkan_h[i] + tenkan_l[i]) / 2.0;
        }
        if !kijun_h[i].is_nan() && !kijun_l[i].is_nan() {
            kijun[i] = (kijun_h[i] + kijun_l[i]) / 2.0;
        }
        if !span_b_h[i].is_nan() && !span_b_l[i].is_nan() {
            span_b[i] = (span_b_h[i] + span_b_l[i]) / 2.0;
        }
    }

    for i in 0..n {
        if !tenkan[i].is_nan() && !kijun[i].is_nan() {
            let target = i + displacement;
            if target < n {
                span_a[target] = (tenkan[i] + kijun[i]) / 2.0;
            }
        }
        if !span_b[i].is_nan() {
            let target = i + displacement;
            if target < n {
                span_b[target] = span_b[i];
            }
        }
        if i >= displacement {
            chikou[i - displacement] = close[i];
        }
    }

    (tenkan, kijun, span_a, span_b, chikou)
}

pub fn fisher(high: &[f64], low: &[f64], period: usize) -> (Vec<f64>, Vec<f64>) {
    let n = high.len();
    let mut fisher = vec![f64::NAN; n];
    let mut signal = vec![f64::NAN; n];
    if n == 0 || low.len() != n || period == 0 {
        return (fisher, signal);
    }

    let mut hl2 = vec![0.0; n];
    for i in 0..n {
        hl2[i] = (high[i] + low[i]) / 2.0;
    }
    let h_max = crate::rolling::rolling_max(&hl2, period);
    let l_min = crate::rolling::rolling_min(&hl2, period);

    let mut prev_value = 0.0;
    let mut prev_fisher = 0.0;
    for i in 0..n {
        if h_max[i].is_nan() || l_min[i].is_nan() {
            continue;
        }
        let diff = h_max[i] - l_min[i];
        let x = if diff == 0.0 {
            0.0
        } else {
            ((hl2[i] - l_min[i]) / diff) - 0.5
        };
        let mut value = 0.66 * x + 0.67 * prev_value;
        value = value.clamp(-0.999, 0.999);
        let f = 0.5 * ((1.0 + value) / (1.0 - value)).ln() + 0.5 * prev_fisher;
        fisher[i] = f;
        prev_value = value;
        prev_fisher = f;
    }

    for i in 1..n {
        signal[i] = fisher[i - 1];
    }
    if n > 0 {
        signal[0] = 0.0;
    }
    (fisher, signal)
}

pub fn psar(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    af_start: f64,
    af_increment: f64,
    af_max: f64,
) -> (Vec<f64>, Vec<f64>) {
    let n = close.len();
    let mut sar = vec![f64::NAN; n];
    let mut direction = vec![f64::NAN; n];
    if n == 0 || high.len() != n || low.len() != n {
        return (sar, direction);
    }
    if n == 1 {
        sar[0] = low[0];
        direction[0] = 1.0;
        return (sar, direction);
    }

    let mut is_long = close[1] >= close[0];
    let mut af = af_start;
    let mut ep = if is_long { high[0] } else { low[0] };
    sar[0] = if is_long { low[0] } else { high[0] };
    direction[0] = if is_long { 1.0 } else { -1.0 };

    for i in 1..n {
        let mut curr = sar[i - 1] + af * (ep - sar[i - 1]);
        if is_long {
            curr = curr.min(low[i - 1]);
            if i > 1 {
                curr = curr.min(low[i - 2]);
            }
            if low[i] < curr {
                is_long = false;
                curr = ep;
                ep = low[i];
                af = af_start;
            } else if high[i] > ep {
                ep = high[i];
                af = (af + af_increment).min(af_max);
            }
        } else {
            curr = curr.max(high[i - 1]);
            if i > 1 {
                curr = curr.max(high[i - 2]);
            }
            if high[i] > curr {
                is_long = true;
                curr = ep;
                ep = high[i];
                af = af_start;
            } else if low[i] < ep {
                ep = low[i];
                af = (af + af_increment).min(af_max);
            }
        }
        sar[i] = curr;
        direction[i] = if is_long { 1.0 } else { -1.0 };
    }
    (sar, direction)
}

pub fn supertrend(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
    multiplier: f64,
) -> (Vec<f64>, Vec<f64>) {
    let n = close.len();
    let mut st = vec![f64::NAN; n];
    let mut direction = vec![f64::NAN; n];
    if n == 0 || high.len() != n || low.len() != n || period == 0 {
        return (st, direction);
    }

    let atr = crate::volatility::atr(high, low, close, period);
    let mut final_upper = vec![f64::NAN; n];
    let mut final_lower = vec![f64::NAN; n];
    let mut basic_upper = vec![f64::NAN; n];
    let mut basic_lower = vec![f64::NAN; n];

    for i in 0..n {
        if atr[i].is_nan() {
            continue;
        }
        let hl2 = (high[i] + low[i]) / 2.0;
        basic_upper[i] = hl2 + multiplier * atr[i];
        basic_lower[i] = hl2 - multiplier * atr[i];
    }

    for i in 0..n {
        if i == 0 || basic_upper[i].is_nan() || basic_lower[i].is_nan() {
            final_upper[i] = basic_upper[i];
            final_lower[i] = basic_lower[i];
            continue;
        }
        if final_upper[i - 1].is_nan() || final_lower[i - 1].is_nan() {
            final_upper[i] = basic_upper[i];
            final_lower[i] = basic_lower[i];
            continue;
        }
        final_upper[i] = if basic_upper[i] < final_upper[i - 1] || close[i - 1] > final_upper[i - 1] {
            basic_upper[i]
        } else {
            final_upper[i - 1]
        };
        final_lower[i] = if basic_lower[i] > final_lower[i - 1] || close[i - 1] < final_lower[i - 1] {
            basic_lower[i]
        } else {
            final_lower[i - 1]
        };
    }

    let start = basic_upper
        .iter()
        .zip(final_upper.iter())
        .position(|(b, f)| !b.is_nan() && !f.is_nan());
    let Some(start_idx) = start else {
        return (st, direction);
    };

    st[start_idx] = final_upper[start_idx];
    direction[start_idx] = -1.0;

    for i in (start_idx + 1)..n {
        if basic_upper[i].is_nan() || final_upper[i].is_nan() || final_lower[i].is_nan() {
            continue;
        }
        if st[i - 1] == final_upper[i - 1] {
            if close[i] <= final_upper[i] {
                st[i] = final_upper[i];
                direction[i] = -1.0;
            } else {
                st[i] = final_lower[i];
                direction[i] = 1.0;
            }
        } else if close[i] >= final_lower[i] {
            st[i] = final_lower[i];
            direction[i] = 1.0;
        } else {
            st[i] = final_upper[i];
            direction[i] = -1.0;
        }
    }

    (st, direction)
}
