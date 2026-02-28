pub fn crossup(a: &[f64], b: &[f64]) -> Vec<bool> {
    let n = a.len().min(b.len());
    let mut out = vec![false; n];
    if n < 2 {
        return out;
    }
    for i in 1..n {
        out[i] = a[i] > b[i] && a[i - 1] <= b[i - 1];
    }
    out
}

pub fn crossdown(a: &[f64], b: &[f64]) -> Vec<bool> {
    let n = a.len().min(b.len());
    let mut out = vec![false; n];
    if n < 2 {
        return out;
    }
    for i in 1..n {
        out[i] = a[i] < b[i] && a[i - 1] >= b[i - 1];
    }
    out
}

pub fn cross(a: &[f64], b: &[f64]) -> Vec<bool> {
    let up = crossup(a, b);
    let down = crossdown(a, b);
    up.iter()
        .zip(down.iter())
        .map(|(u, d)| *u || *d)
        .collect::<Vec<bool>>()
}

pub fn rising(a: &[f64]) -> Vec<bool> {
    let n = a.len();
    let mut out = vec![false; n];
    if n < 2 {
        return out;
    }
    for i in 1..n {
        out[i] = a[i] > a[i - 1];
    }
    out
}

pub fn falling(a: &[f64]) -> Vec<bool> {
    let n = a.len();
    let mut out = vec![false; n];
    if n < 2 {
        return out;
    }
    for i in 1..n {
        out[i] = a[i] < a[i - 1];
    }
    out
}

pub fn rising_pct(a: &[f64], pct: f64) -> Vec<bool> {
    let n = a.len();
    let mut out = vec![false; n];
    if n < 2 {
        return out;
    }
    let m = 1.0 + (pct / 100.0);
    for i in 1..n {
        out[i] = a[i] >= a[i - 1] * m;
    }
    out
}

pub fn falling_pct(a: &[f64], pct: f64) -> Vec<bool> {
    let n = a.len();
    let mut out = vec![false; n];
    if n < 2 {
        return out;
    }
    let m = 1.0 - (pct / 100.0);
    for i in 1..n {
        out[i] = a[i] <= a[i - 1] * m;
    }
    out
}

pub fn in_channel(price: &[f64], upper: &[f64], lower: &[f64]) -> Vec<bool> {
    let n = price.len().min(upper.len()).min(lower.len());
    let mut out = vec![false; n];
    for i in 0..n {
        out[i] = price[i] >= lower[i] && price[i] <= upper[i];
    }
    out
}

pub fn out_channel(price: &[f64], upper: &[f64], lower: &[f64]) -> Vec<bool> {
    let n = price.len().min(upper.len()).min(lower.len());
    let mut out = vec![false; n];
    for i in 0..n {
        out[i] = price[i] > upper[i] || price[i] < lower[i];
    }
    out
}

pub fn enter_channel(price: &[f64], upper: &[f64], lower: &[f64]) -> Vec<bool> {
    let n = price.len().min(upper.len()).min(lower.len());
    let mut out = vec![false; n];
    if n < 2 {
        return out;
    }
    for i in 1..n {
        let curr_in = price[i] >= lower[i] && price[i] <= upper[i];
        let prev_out = price[i - 1] > upper[i - 1] || price[i - 1] < lower[i - 1];
        out[i] = curr_in && prev_out;
    }
    out
}

pub fn exit_channel(price: &[f64], upper: &[f64], lower: &[f64]) -> Vec<bool> {
    let n = price.len().min(upper.len()).min(lower.len());
    let mut out = vec![false; n];
    if n < 2 {
        return out;
    }
    for i in 1..n {
        let curr_out = price[i] > upper[i] || price[i] < lower[i];
        let prev_in = price[i - 1] >= lower[i - 1] && price[i - 1] <= upper[i - 1];
        out[i] = curr_out && prev_in;
    }
    out
}
