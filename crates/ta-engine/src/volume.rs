pub fn obv(close: &[f64], volume: &[f64]) -> Vec<f64> {
    let n = close.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || volume.len() != n {
        return out;
    }

    out[0] = volume[0];
    for i in 1..n {
        out[i] = if close[i] > close[i - 1] {
            out[i - 1] + volume[i]
        } else if close[i] < close[i - 1] {
            out[i - 1] - volume[i]
        } else {
            out[i - 1]
        };
    }
    out
}

pub fn klinger_vf(high: &[f64], low: &[f64], close: &[f64], volume: &[f64]) -> Vec<f64> {
    let n = close.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || high.len() != n || low.len() != n || volume.len() != n {
        return out;
    }

    let mut prev_tp: Option<f64> = None;

    for i in 0..n {
        let tp = (high[i] + low[i] + close[i]) / 3.0;
        let dm = high[i] - low[i];

        if prev_tp.is_none() {
            out[i] = 0.0;
            prev_tp = Some(tp);
            continue;
        }

        let trend = if tp > prev_tp.unwrap_or(tp) {
            1.0
        } else {
            -1.0
        };
        let safe_dm = if dm > 0.0 { dm } else { 1e-10 };

        let vf = volume[i]
            * (2.0 * ((tp - prev_tp.unwrap_or(tp)) / safe_dm) - 1.0).abs()
            * trend
            * 100.0;
        out[i] = vf;
        prev_tp = Some(tp);
    }

    out
}

pub fn cmf(high: &[f64], low: &[f64], close: &[f64], volume: &[f64], period: usize) -> Vec<f64> {
    let n = close.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || period == 0 || high.len() != n || low.len() != n || volume.len() != n {
        return out;
    }

    let mut mfv = vec![0.0; n];
    for i in 0..n {
        let hl = high[i] - low[i];
        if hl == 0.0 {
            mfv[i] = 0.0;
            continue;
        }
        let mfm = ((close[i] - low[i]) - (high[i] - close[i])) / hl;
        mfv[i] = mfm * volume[i];
    }

    let mut sum_mfv = 0.0;
    let mut sum_vol = 0.0;
    for i in 0..n {
        sum_mfv += mfv[i];
        sum_vol += volume[i];

        if i >= period {
            sum_mfv -= mfv[i - period];
            sum_vol -= volume[i - period];
        }

        if i + 1 >= period {
            out[i] = if sum_vol == 0.0 {
                0.0
            } else {
                sum_mfv / sum_vol
            };
        }
    }

    out
}

pub fn vwap(high: &[f64], low: &[f64], close: &[f64], volume: &[f64]) -> Vec<f64> {
    let n = close.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || high.len() != n || low.len() != n || volume.len() != n {
        return out;
    }

    let mut sum_pv = 0.0;
    let mut sum_vol = 0.0;

    for i in 0..n {
        let tp = (high[i] + low[i] + close[i]) / 3.0;
        sum_pv += tp * volume[i];
        sum_vol += volume[i];

        if sum_vol > 0.0 {
            out[i] = sum_pv / sum_vol;
        } else {
            out[i] = tp;
        }
    }

    out
}

pub fn klinger(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    volume: &[f64],
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> (Vec<f64>, Vec<f64>) {
    let vf = klinger_vf(high, low, close, volume);
    let ema_fast = crate::moving_averages::ema(&vf, fast_period);
    let ema_slow = crate::moving_averages::ema(&vf, slow_period);
    let n = close.len();
    let mut klinger_line = vec![f64::NAN; n];
    for i in 0..n {
        if !ema_fast[i].is_nan() && !ema_slow[i].is_nan() {
            klinger_line[i] = ema_fast[i] - ema_slow[i];
        }
    }
    let signal = crate::moving_averages::ema(&klinger_line, signal_period);
    (klinger_line, signal)
}
