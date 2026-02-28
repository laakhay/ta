pub fn rolling_sum(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if period == 0 || n == 0 {
        return out;
    }

    let mut sum = 0.0;
    for i in 0..n {
        sum += values[i];
        if i >= period {
            sum -= values[i - period];
        }
        if i + 1 >= period {
            out[i] = sum;
        }
    }
    out
}

pub fn rolling_mean(values: &[f64], period: usize) -> Vec<f64> {
    let mut out = rolling_sum(values, period);
    if period == 0 {
        return out;
    }
    let p = period as f64;
    for x in &mut out {
        if !x.is_nan() {
            *x /= p;
        }
    }
    out
}

pub fn rolling_std(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if period == 0 || n == 0 {
        return out;
    }

    let mut sum = 0.0;
    let mut sumsq = 0.0;

    for i in 0..n {
        let x = values[i];
        sum += x;
        sumsq += x * x;

        if i >= period {
            let d = values[i - period];
            sum -= d;
            sumsq -= d * d;
        }

        if i + 1 >= period {
            let mean = sum / period as f64;
            let mut var = (sumsq / period as f64) - (mean * mean);
            if var < 0.0 {
                var = 0.0;
            }
            out[i] = var.sqrt();
        }
    }

    out
}

pub fn rolling_min(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if period == 0 || n == 0 {
        return out;
    }

    for i in 0..n {
        if i + 1 >= period {
            let start = i + 1 - period;
            let mut m = values[start];
            for x in &values[start + 1..=i] {
                if *x < m {
                    m = *x;
                }
            }
            out[i] = m;
        }
    }

    out
}

pub fn rolling_max(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if period == 0 || n == 0 {
        return out;
    }

    for i in 0..n {
        if i + 1 >= period {
            let start = i + 1 - period;
            let mut m = values[start];
            for x in &values[start + 1..=i] {
                if *x > m {
                    m = *x;
                }
            }
            out[i] = m;
        }
    }

    out
}

pub fn ema(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || period == 0 {
        return out;
    }

    let alpha = 2.0 / (period as f64 + 1.0);
    out[0] = values[0];

    for i in 1..n {
        out[i] = alpha * values[i] + (1.0 - alpha) * out[i - 1];
    }

    out
}

pub fn rma(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || period == 0 {
        return out;
    }

    let alpha = 1.0 / period as f64;
    out[0] = values[0];

    for i in 1..n {
        out[i] = alpha * values[i] + (1.0 - alpha) * out[i - 1];
    }

    out
}

pub fn wma(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 || period == 0 {
        return out;
    }

    let denom = (period * (period + 1) / 2) as f64;

    for i in 0..n {
        if i + 1 >= period {
            let start = i + 1 - period;
            let mut weighted_sum = 0.0;
            for (idx, x) in values[start..=i].iter().enumerate() {
                let w = (idx + 1) as f64;
                weighted_sum += *x * w;
            }
            out[i] = weighted_sum / denom;
        }
    }

    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rolling_sum_smoke() {
        let out = rolling_sum(&[1.0, 2.0, 3.0, 4.0], 3);
        assert!(out[0].is_nan());
        assert!(out[1].is_nan());
        assert_eq!(out[2], 6.0);
        assert_eq!(out[3], 9.0);
    }

    #[test]
    fn ema_smoke() {
        let out = ema(&[1.0, 2.0, 3.0], 3);
        assert_eq!(out[0], 1.0);
        assert_eq!(out[1], 1.5);
        assert_eq!(out[2], 2.25);
    }
}
